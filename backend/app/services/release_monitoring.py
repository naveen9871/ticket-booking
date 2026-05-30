from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models import Movie, Notification, ReleaseSubscription, Showtime
from app.services.discovery import discover_showtimes
from app.services.intent import parse_intent
from app.services.seat_recommendation import rank_seat_blocks


def create_release_subscription(
    session: Session,
    *,
    session_key: str,
    movie_title: str,
    city: str,
    user_id: int | None = None,
    preferred_formats: list[str] | None = None,
    preferred_theatres: list[str] | None = None,
    price_ceiling: float | None = None,
    party_size: int = 2,
    auto_reserve: bool = False,
) -> ReleaseSubscription:
    subscription = ReleaseSubscription(
        user_id=user_id,
        session_key=session_key,
        movie_title=movie_title,
        city=city,
        preferred_formats=json.dumps(preferred_formats or []),
        preferred_theatres=json.dumps(preferred_theatres or []),
        price_ceiling=price_ceiling,
        party_size=party_size,
        auto_reserve=auto_reserve,
    )
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return subscription


def evaluate_subscription(session: Session, subscription: ReleaseSubscription) -> dict[str, Any]:
    intent = parse_intent(
        session,
        f"Find {subscription.party_size} tickets for {subscription.movie_title} in {subscription.city}",
        context={"city": subscription.city},
        profile={
            "price_ceiling": subscription.price_ceiling,
            "formats": json.loads(subscription.preferred_formats),
            "theatres": json.loads(subscription.preferred_theatres),
        },
    )
    intent["movie"] = subscription.movie_title
    intent["city"] = subscription.city
    intent["party_size"] = subscription.party_size
    candidates = discover_showtimes(session, intent)
    ranked_candidates = sorted(candidates, key=lambda item: (-item.get("discovery_score", 0), item["base_price"]))
    seat_recs = None
    if ranked_candidates:
        seat_recs = rank_seat_blocks(
            session,
            ranked_candidates[0]["id"],
            subscription.party_size,
            {"price_ceiling": subscription.price_ceiling, "base_price": ranked_candidates[0]["base_price"]},
            session_key=subscription.session_key,
        )

    subscription.last_checked_at = datetime.utcnow()
    subscription.updated_at = datetime.utcnow()
    session.add(subscription)

    if ranked_candidates:
        notification = Notification(
            user_id=subscription.user_id,
            title=f"Bookings open for {subscription.movie_title}",
            message=f"{ranked_candidates[0]['theatre_name']} has seats in {subscription.city}.",
            metadata_json=json.dumps({"subscription_id": subscription.id, "showtime_id": ranked_candidates[0]["id"]}),
        )
        session.add(notification)
    session.commit()

    return {
        "subscription_id": subscription.id,
        "status": "MATCH_FOUND" if ranked_candidates else "WAITING",
        "matches": ranked_candidates[:5],
        "seat_recommendations": seat_recs,
        "auto_reserve_enabled": subscription.auto_reserve,
    }


def run_release_monitor_cycle(session: Session, limit: int = 25) -> dict[str, Any]:
    active = session.exec(select(ReleaseSubscription).where(ReleaseSubscription.status == "ACTIVE").limit(limit)).all()
    results = [evaluate_subscription(session, subscription) for subscription in active]
    return {
        "checked": len(active),
        "matches": sum(1 for item in results if item["status"] == "MATCH_FOUND"),
        "results": results,
    }


def booking_demand_snapshot(session: Session) -> dict[str, Any]:
    movies = session.exec(select(Movie)).all()
    showtimes = session.exec(select(Showtime)).all()
    active_subscriptions = session.exec(select(ReleaseSubscription).where(ReleaseSubscription.status == "ACTIVE")).all()
    watched_titles = {subscription.movie_title.lower() for subscription in active_subscriptions}
    upcoming_movies = [movie.title for movie in movies if movie.title.lower() in watched_titles]
    return {
        "movie_count": len(movies),
        "showtime_count": len(showtimes),
        "active_release_watches": len(active_subscriptions),
        "watched_movies_with_inventory": upcoming_movies,
        "risk_level": "SPIKE_READY" if len(active_subscriptions) > 1000 else "NORMAL",
    }
