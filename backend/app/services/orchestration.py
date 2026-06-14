from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlmodel import Session

from app.services.discovery import discover_showtimes
from app.services.intent import parse_intent
from app.services.planning import generate_plans
from app.services.preferences import get_or_create_memory, load_profile, update_memory_from_intent
from app.services.recovery import build_recovery_message, normalize_failure
from app.services.release_monitoring import create_release_subscription
from app.services.retry_engine import dynamic_replan, suggest_alternatives
from app.services.workflow import (
    create_agent_session,
    log_workflow_event,
    replace_plans,
    update_agent_session,
)


def ensure_session_key(context: dict[str, Any] | None) -> str:
    context = context or {}
    session_key = context.get("session_key")
    if session_key:
        return session_key
    return f"guest-{uuid4().hex[:12]}"


def run_agentic_planning(
    session: Session,
    user_id: int | None,
    message: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = context or {}
    session_key = ensure_session_key(context)
    memory = get_or_create_memory(session, session_key, user_id)
    profile = load_profile(memory)
    agent_session = create_agent_session(
        session,
        session_key=session_key,
        user_id=user_id,
        workflow_type="EVENT_BOOKING",
        context=context,
    )

    trace: list[dict[str, str]] = []

    try:
        log_workflow_event(session, agent_session.id, "intent-agent", "INTENT_PARSE_STARTED", "RUNNING")
        intent = parse_intent(session, message, context=context, profile=profile)
        update_memory_from_intent(session, memory, intent, message)
        trace.append({"agent": "Intent Agent", "status": "done", "detail": intent["summary"]})
        log_workflow_event(session, agent_session.id, "intent-agent", "INTENT_PARSE_COMPLETED", "COMPLETED", intent)
        update_agent_session(session, agent_session, status="RUNNING", current_stage="DISCOVERY", context={**context, "intent": intent})

        if intent.get("kind") == "watch":
            log_workflow_event(session, agent_session.id, "watch-agent", "SUBSCRIPTION_STARTED", "RUNNING")
            movie_title = intent.get("movie")
            if not movie_title:
                update_agent_session(session, agent_session, status="FAILED", last_error="Movie title not identified")
                return {
                    "type": "message",
                    "message": "I couldn't identify the movie title. Please mention the movie name clearly — e.g. 'Alert me when Pushpa 3 bookings open'.",
                    "context": {"session_key": session_key},
                    "trace": trace,
                }
            subscription = create_release_subscription(
                session,
                session_key=session_key,
                user_id=user_id,
                movie_title=movie_title,
                city=intent.get("city") or "Bengaluru",
                party_size=intent.get("party_size", 2),
            )
            trace.append({"agent": "Watch Agent", "status": "done", "detail": f"Set a release watch for {movie_title} in {subscription.city}."})
            log_workflow_event(session, agent_session.id, "watch-agent", "SUBSCRIPTION_COMPLETED", "COMPLETED", {"id": subscription.id})
            update_agent_session(session, agent_session, status="COMPLETED", current_stage="NOTIFY")
            
            return {
                "type": "message",
                "message": f"Understood! I've set a release watch for **{movie_title}** in **{subscription.city}**. I'll monitor partner theatres and notify you the moment bookings open.",
                "context": {"session_key": session_key},
                "trace": trace,
            }

        log_workflow_event(session, agent_session.id, "discovery-agent", "DISCOVERY_STARTED", "RUNNING")
        candidates = discover_showtimes(session, intent)
        trace.append({"agent": "Discovery Agent", "status": "done", "detail": f"Found {len(candidates)} candidate showtimes."})
        log_workflow_event(session, agent_session.id, "discovery-agent", "DISCOVERY_COMPLETED", "COMPLETED", {"count": len(candidates)})
        update_agent_session(session, agent_session, current_stage="PLANNING")

        if not candidates:
            update_agent_session(session, agent_session, status="FAILED", last_error="No matching inventory")
            trace.append({"agent": "Recovery Agent", "status": "done", "detail": "No exact matches — trying relaxed constraints."})

            # Try alternatives with relaxed budget / format / time
            alt = suggest_alternatives(session, intent)
            if alt["status"] == "alternatives_found":
                alt_candidates = alt["suggestions"]
                alt_plans = generate_plans(session, intent, alt_candidates)
                saved_alt = replace_plans(session, agent_session.id, alt_plans)
                trace.append({"agent": "Recovery Agent", "status": "done", "detail": f"Found {len(alt_candidates)} relaxed alternative(s)."})
                budget_note = f"under ₹{intent['budget_max']}" if intent.get("budget_max") else ""
                relaxed = alt.get("relaxed_constraints", {})
                relaxed_parts = []
                if relaxed.get("budget"):
                    relaxed_parts.append("budget")
                if relaxed.get("format"):
                    relaxed_parts.append("format")
                if relaxed.get("time"):
                    relaxed_parts.append("timing")
                relaxed_str = f" (relaxed {', '.join(relaxed_parts)})" if relaxed_parts else ""
                return {
                    "type": "agent_plan",
                    "message": (
                        f"I couldn't find exact matches{f' {budget_note}' if budget_note else ''}, "
                        f"but here are the closest alternatives{relaxed_str}:"
                    ),
                    "data": {
                        "intent": intent,
                        "plans": alt_plans,
                        "top_candidates": alt_candidates[:6],
                        "fallback": True,
                    },
                    "context": {"session_key": session_key, "city": intent.get("city"), "seat_count": intent.get("party_size", 2)},
                    "trace": trace,
                }

            return {
                **build_recovery_message(intent, "no matching shows were available even after broadening the search"),
                "context": {"session_key": session_key, "city": intent.get("city"), "seat_count": intent.get("party_size", 2)},
                "trace": trace,
            }

        log_workflow_event(session, agent_session.id, "planning-agent", "PLANNING_STARTED", "RUNNING")
        plans = generate_plans(session, intent, candidates)
        saved_plans = replace_plans(session, agent_session.id, plans)
        trace.append({"agent": "Planning Agent", "status": "done", "detail": f"Prepared {len(saved_plans)} plan options."})
        log_workflow_event(session, agent_session.id, "planning-agent", "PLANNING_COMPLETED", "COMPLETED", {"plans": len(saved_plans)})
        update_agent_session(
            session,
            agent_session,
            status="AWAITING_USER",
            current_stage="APPROVAL",
            context={**context, "intent": intent, "plans": [plan.id for plan in saved_plans]},
        )

        return {
            "type": "agent_plan",
            "message": "I built three booking strategies so you can choose speed, value, or a more premium experience.",
            "data": {
                "intent": intent,
                "plans": plans,
                "top_candidates": candidates[:6],
            },
            "context": {
                "session_key": session_key,
                "city": intent.get("city"),
                "seat_count": intent.get("party_size", 2),
                "intent_kind": intent.get("kind"),
            },
            "trace": trace,
        }
    except Exception as exc:
        error_text = normalize_failure(exc)
        update_agent_session(session, agent_session, status="FAILED", current_stage="RECOVERY", last_error=error_text)
        log_workflow_event(session, agent_session.id, "recovery-agent", "WORKFLOW_FAILED", "FAILED", {"error": error_text})
        trace.append({"agent": "Recovery Agent", "status": "done", "detail": "Captured the failure and prepared a safe fallback."})
        fallback_intent = context.get("intent") or {}
        return {
            **build_recovery_message(fallback_intent, error_text),
            "context": {"session_key": session_key, "city": fallback_intent.get("city"), "seat_count": fallback_intent.get("party_size", 2)},
            "trace": trace,
        }
