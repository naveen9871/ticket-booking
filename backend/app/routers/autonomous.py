from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.deps import get_current_user, get_optional_user
from app.db import get_session
from app.models import User
from app.services.cancellation_sniper import (
    cancel_snipe_watch,
    create_snipe_watch,
    run_snipe_cycle,
)
from app.services.provider_adapters import ProviderRequest, provider_registry
from app.services.release_monitoring import (
    booking_demand_snapshot,
    create_release_subscription,
    run_release_monitor_cycle,
)
from app.services.retry_engine import dynamic_replan, suggest_alternatives
from app.services.seat_recommendation import rank_seat_blocks

router = APIRouter(prefix="/autonomous", tags=["autonomous-booking"])


class SeatRecommendationRequest(BaseModel):
    showtime_id: int
    party_size: int = Field(default=2, ge=1, le=10)
    session_key: str | None = None
    price_ceiling: float | None = None
    ideal_row_ratio: float = Field(default=0.62, ge=0.1, le=0.95)


class ReleaseWatchRequest(BaseModel):
    movie_title: str
    city: str = "Bengaluru"
    session_key: str | None = None
    preferred_formats: list[str] = []
    preferred_theatres: list[str] = []
    price_ceiling: float | None = None
    party_size: int = Field(default=2, ge=1, le=10)
    auto_reserve: bool = False
    # FULLY_AUTONOMOUS | APPROVAL_REQUIRED | NOTIFY_ONLY
    execution_mode: str = "NOTIFY_ONLY"


class SnipeWatchRequest(BaseModel):
    showtime_id: int
    party_size: int = Field(default=2, ge=1, le=10)
    session_key: str | None = None
    price_ceiling: float | None = None
    auto_snipe: bool = True


class AlternativesRequest(BaseModel):
    intent: dict
    relax_budget: bool = True
    relax_format: bool = True
    relax_time: bool = True


class ProviderProbeRequest(BaseModel):
    provider_code: str = "BMS_DEMO"
    payload: dict = {}


@router.post("/seat-recommendations")
def recommend_seats(
    payload: SeatRecommendationRequest,
    session: Session = Depends(get_session),
):
    return rank_seat_blocks(
        session,
        payload.showtime_id,
        payload.party_size,
        {
            "price_ceiling": payload.price_ceiling,
            "ideal_row_ratio": payload.ideal_row_ratio,
        },
        session_key=payload.session_key,
    )


@router.post("/release-watch")
def create_release_watch(
    payload: ReleaseWatchRequest,
    session: Session = Depends(get_session),
    user: User | None = Depends(get_optional_user),
):
    subscription = create_release_subscription(
        session,
        session_key=payload.session_key or f"watch-{uuid4().hex[:12]}",
        movie_title=payload.movie_title,
        city=payload.city,
        user_id=user.id if user else None,
        preferred_formats=payload.preferred_formats,
        preferred_theatres=payload.preferred_theatres,
        price_ceiling=payload.price_ceiling,
        party_size=payload.party_size,
        auto_reserve=payload.auto_reserve,
        execution_mode=payload.execution_mode,
    )
    mode_desc = {
        "FULLY_AUTONOMOUS": "I will auto-book seats the moment they open — no approval needed.",
        "APPROVAL_REQUIRED": "I will find seats and ask you to confirm before booking.",
        "NOTIFY_ONLY": "I will alert you when bookings open so you can book manually.",
    }.get(subscription.execution_mode, "")
    return {
        "subscription_id": subscription.id,
        "status": subscription.status,
        "execution_mode": subscription.execution_mode,
        "message": f"Release watch created. {mode_desc}",
    }


# ---------------------------------------------------------------------------
# Cancellation Sniping (Section 6.5)
# ---------------------------------------------------------------------------

@router.post("/snipe-watch")
def create_snipe_watch_endpoint(
    payload: SnipeWatchRequest,
    session: Session = Depends(get_session),
    user: User | None = Depends(get_optional_user),
):
    """Watch a sold-out showtime and snipe released seats automatically."""
    watch = create_snipe_watch(
        session,
        showtime_id=payload.showtime_id,
        user_id=user.id if user else None,
        session_key=payload.session_key or f"snipe-{uuid4().hex[:12]}",
        party_size=payload.party_size,
        price_ceiling=payload.price_ceiling,
        auto_snipe=payload.auto_snipe,
    )
    action = "auto-snipe and hold" if watch.auto_snipe else "notify"
    return {
        "watch_id": watch.id,
        "showtime_id": watch.showtime_id,
        "status": watch.status,
        "message": f"Snipe watch active. I will {action} the moment seats free up.",
    }


@router.delete("/snipe-watch/{watch_id}")
def cancel_snipe_watch_endpoint(
    watch_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        watch = cancel_snipe_watch(session, watch_id, user.id)
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(exc))
    return {"watch_id": watch.id, "status": watch.status}


@router.post("/snipe-watch/run-cycle")
def run_snipe_cycle_endpoint(session: Session = Depends(get_session)):
    """Trigger a snipe evaluation cycle (called by scheduler or Kafka tick)."""
    return run_snipe_cycle(session)


# ---------------------------------------------------------------------------
# Alternatives & Dynamic Replan (Section 6.6)
# ---------------------------------------------------------------------------

@router.post("/alternatives")
def get_alternatives(
    payload: AlternativesRequest,
    session: Session = Depends(get_session),
):
    """Suggest alternative showtimes with relaxed constraints."""
    return suggest_alternatives(
        session,
        payload.intent,
        relax_budget=payload.relax_budget,
        relax_format=payload.relax_format,
        relax_time=payload.relax_time,
    )


@router.post("/replan")
def replan(
    payload: dict,
    session: Session = Depends(get_session),
):
    """Dynamically replan after a booking failure."""
    intent = payload.get("intent", {})
    reason = payload.get("failure_reason", "unknown")
    return dynamic_replan(session, intent, reason)


@router.post("/release-watch/run-cycle")
def run_release_watch_cycle(session: Session = Depends(get_session)):
    return run_release_monitor_cycle(session)


@router.get("/ops/dashboard")
def ops_dashboard(session: Session = Depends(get_session)):
    return {
        "demand": booking_demand_snapshot(session),
        "providers": provider_registry.list_codes(),
        "queues": {
            "booking.reserve.requested": "ready",
            "booking.reserve.completed": "ready",
            "release.monitor.tick": "ready",
            "notification.dispatch.requested": "ready",
        },
        "slo": {
            "seat_hold_ttl_seconds": 180,
            "target_booking_latency_ms": 1200,
            "target_recommendation_latency_ms": 250,
        },
    }


@router.post("/providers/probe")
def provider_probe(payload: ProviderProbeRequest):
    try:
        adapter = provider_registry.get(payload.provider_code)
    except KeyError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unknown provider: {payload.provider_code}. Available: {provider_registry.list_codes()}")
    request = ProviderRequest(provider_code=payload.provider_code, correlation_id=str(uuid4()), payload=payload.payload)
    return adapter.search_showtimes(request)
