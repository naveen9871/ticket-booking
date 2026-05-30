from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.deps import get_optional_user
from app.db import get_session
from app.models import User
from app.services.provider_adapters import ProviderRequest, provider_registry
from app.services.release_monitoring import (
    booking_demand_snapshot,
    create_release_subscription,
    run_release_monitor_cycle,
)
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
    )
    return {
        "subscription_id": subscription.id,
        "status": subscription.status,
        "message": "Release watch created. Monitoring can be run by scheduler, Kafka consumer, or the demo cycle endpoint.",
    }


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
    adapter = provider_registry.get(payload.provider_code)
    request = ProviderRequest(provider_code=payload.provider_code, correlation_id=str(uuid4()), payload=payload.payload)
    return adapter.search_showtimes(request)
