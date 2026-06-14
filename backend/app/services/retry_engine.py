"""
Intelligent Retry & Fallback Engine (Section 6.6).

On booking failure the engine can:
  1. Retry reservation (same showtime, different seats if needed)
  2. Retry payment (idempotent re-submit)
  3. Switch providers (alternate adapter)
  4. Suggest alternatives (nearby showtimes / theatres)
  5. Dynamically replan (re-run discovery + planning with relaxed constraints)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlmodel import Session, select

from app.models import BookingAttempt, Notification, Showtime
from app.services.discovery import discover_showtimes
from app.services.planning import generate_plans
from app.services.provider_adapters import ProviderRequest, provider_registry
from app.services.seats import auto_select_seats, create_seat_hold, get_seat_map

MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_BASE_MS = 500     # 500ms → 1s → 2s


# ---------------------------------------------------------------------------
# Attempt tracking helpers
# ---------------------------------------------------------------------------

def _log_attempt(
    session: Session,
    *,
    showtime_id: int,
    user_id: int | None,
    idempotency_key: str,
    attempt_no: int,
    status: str,
    error_code: str | None = None,
    error_message: str | None = None,
    latency_ms: int | None = None,
    booking_id: int | None = None,
) -> BookingAttempt:
    attempt = BookingAttempt(
        booking_id=booking_id,
        showtime_id=showtime_id,
        user_id=user_id,
        idempotency_key=idempotency_key,
        attempt_no=attempt_no,
        status=status,
        error_code=error_code,
        error_message=error_message,
        latency_ms=latency_ms,
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    return attempt


# ---------------------------------------------------------------------------
# Core retry loop — reservation
# ---------------------------------------------------------------------------

def retry_reservation(
    session: Session,
    *,
    showtime_id: int,
    user_id: int | None,
    session_key: str,
    party_size: int,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """
    Attempt to hold seats up to MAX_RETRY_ATTEMPTS times with exponential backoff.
    Returns the successful hold or a structured failure.
    """
    idem_key = idempotency_key or f"retry-{uuid4().hex}"
    last_error: str = "unknown error"

    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        start = time.monotonic()
        try:
            seat_map = get_seat_map(session, showtime_id, session_key=session_key)
            seats = auto_select_seats(seat_map, party_size)
            if not seats:
                last_error = "no_available_seats"
                _log_attempt(
                    session, showtime_id=showtime_id, user_id=user_id,
                    idempotency_key=idem_key, attempt_no=attempt,
                    status="FAILED", error_code="NO_SEATS",
                    latency_ms=int((time.monotonic() - start) * 1000),
                )
                break  # No point retrying if no seats exist

            hold = create_seat_hold(
                session,
                showtime_id=showtime_id,
                user_id=user_id,
                session_key=session_key,
                seat_ids=seats,
            )
            latency = int((time.monotonic() - start) * 1000)
            _log_attempt(
                session, showtime_id=showtime_id, user_id=user_id,
                idempotency_key=idem_key, attempt_no=attempt,
                status="SUCCESS", latency_ms=latency,
            )
            return {
                "status": "success",
                "hold_token": hold.hold_token,
                "seats": seats,
                "attempts": attempt,
                "latency_ms": latency,
            }

        except Exception as exc:
            last_error = str(exc)
            latency = int((time.monotonic() - start) * 1000)
            _log_attempt(
                session, showtime_id=showtime_id, user_id=user_id,
                idempotency_key=idem_key, attempt_no=attempt,
                status="FAILED", error_code="EXCEPTION",
                error_message=last_error, latency_ms=latency,
            )
            if attempt < MAX_RETRY_ATTEMPTS:
                backoff_s = (RETRY_BACKOFF_BASE_MS * (2 ** (attempt - 1))) / 1000
                time.sleep(backoff_s)

    return {
        "status": "failed",
        "reason": last_error,
        "attempts": MAX_RETRY_ATTEMPTS,
    }


# ---------------------------------------------------------------------------
# Provider switching
# ---------------------------------------------------------------------------

def retry_with_provider_switch(
    session: Session,
    *,
    original_provider: str,
    showtime_id: int,
    party_size: int,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """
    Try alternate providers when the primary fails.
    Returns first successful response or exhaustion failure.
    """
    corr = correlation_id or str(uuid4())
    codes = provider_registry.list_codes()
    alternates = [c for c in codes if c != original_provider]

    for code in alternates:
        try:
            adapter = provider_registry.get(code)
            req = ProviderRequest(
                provider_code=code,
                correlation_id=corr,
                payload={"showtime_id": showtime_id, "party_size": party_size},
            )
            result = adapter.search_showtimes(req)
            if result.get("showtimes"):
                return {
                    "status": "switched",
                    "provider": code,
                    "data": result,
                }
        except Exception:
            continue

    return {"status": "all_providers_failed", "tried": alternates}


# ---------------------------------------------------------------------------
# Alternative suggestions
# ---------------------------------------------------------------------------

def suggest_alternatives(
    session: Session,
    intent: dict[str, Any],
    *,
    relax_budget: bool = True,
    relax_format: bool = True,
    relax_time: bool = True,
) -> dict[str, Any]:
    """
    Re-run discovery with relaxed constraints to surface alternatives.
    """
    relaxed = dict(intent)

    if relax_budget and intent.get("budget_max"):
        relaxed["budget_max"] = intent["budget_max"] * 1.3   # +30% headroom

    if relax_format:
        relaxed["format"] = None                              # any format

    if relax_time:
        relaxed["time_window"] = None                         # any time

    from app.services.discovery import discover_showtimes as _discover
    candidates = _discover(session, relaxed)

    if not candidates:
        return {"status": "no_alternatives", "suggestions": []}

    return {
        "status": "alternatives_found",
        "suggestions": candidates[:5],
        "relaxed_constraints": {
            "budget": relax_budget,
            "format": relax_format,
            "time": relax_time,
        },
    }


# ---------------------------------------------------------------------------
# Dynamic replan — full re-orchestration with relaxed intent
# ---------------------------------------------------------------------------

def dynamic_replan(
    session: Session,
    intent: dict[str, Any],
    failure_reason: str,
) -> dict[str, Any]:
    """
    After a failure, re-run planning with progressively relaxed constraints.
    Returns new plans or exhaustion message.
    """
    # Step 1: try with loosened budget + format
    alt = suggest_alternatives(session, intent)
    if alt["status"] == "no_alternatives":
        # Step 2: try without city constraint
        relaxed = dict(intent)
        relaxed["city"] = None
        alt = suggest_alternatives(session, relaxed, relax_budget=True, relax_format=True, relax_time=True)

    if alt["status"] == "no_alternatives":
        return {
            "type": "message",
            "message": (
                f"Even after relaxing all constraints I could not find available shows. "
                f"Original failure: {failure_reason}. Try a different movie or check back later."
            ),
        }

    candidates = alt["suggestions"]
    new_plans = generate_plans(session, intent, candidates)
    return {
        "type": "agent_plan",
        "message": (
            f"The original booking failed ({failure_reason}). "
            "Here are the best alternative options I found:"
        ),
        "data": {
            "intent": intent,
            "plans": new_plans,
            "top_candidates": candidates[:6],
            "fallback": True,
            "relaxed": alt.get("relaxed_constraints", {}),
        },
    }
