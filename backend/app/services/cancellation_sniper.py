"""
Cancellation Sniping service (Section 6.5).

Monitors sold-out showtimes for seat releases.
When seats free up (cancelled bookings / expired holds), immediately attempts
to hold them for watchers — with retry on conflict.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from sqlmodel import Session, select

from app.models import Booking, Notification, Screen, SeatHold, Showtime, SoldOutWatch
from app.services.seats import auto_select_seats, create_seat_hold, get_seat_map

MAX_SNIPE_RETRIES = 3
WATCH_TTL_HOURS = 48


# ---------------------------------------------------------------------------
# Watch management
# ---------------------------------------------------------------------------

def create_snipe_watch(
    session: Session,
    *,
    showtime_id: int,
    user_id: int | None = None,
    session_key: str,
    party_size: int = 2,
    price_ceiling: float | None = None,
    auto_snipe: bool = True,
) -> SoldOutWatch:
    existing = session.exec(
        select(SoldOutWatch).where(
            SoldOutWatch.showtime_id == showtime_id,
            SoldOutWatch.session_key == session_key,
            SoldOutWatch.status == "ACTIVE",
        )
    ).first()
    if existing:
        return existing

    watch = SoldOutWatch(
        user_id=user_id,
        session_key=session_key,
        showtime_id=showtime_id,
        party_size=party_size,
        price_ceiling=price_ceiling,
        auto_snipe=auto_snipe,
        status="ACTIVE",
    )
    session.add(watch)
    session.commit()
    session.refresh(watch)
    return watch


def cancel_snipe_watch(session: Session, watch_id: int, user_id: int) -> SoldOutWatch:
    watch = session.get(SoldOutWatch, watch_id)
    if not watch or watch.user_id != user_id:
        raise ValueError("Watch not found")
    watch.status = "CANCELLED"
    watch.updated_at = datetime.utcnow()
    session.add(watch)
    session.commit()
    session.refresh(watch)
    return watch


# ---------------------------------------------------------------------------
# Seat availability check
# ---------------------------------------------------------------------------

def _count_available_seats(session: Session, showtime_id: int) -> int:
    """Count seats that are not booked or actively held."""
    showtime = session.get(Showtime, showtime_id)
    if not showtime:
        return 0

    screen = session.exec(
        select(Screen).where(Screen.id == showtime.screen_id)
    ).first()
    if not screen:
        return 0

    try:
        seat_map = json.loads(screen.seat_map)
    except Exception:
        return 0

    total = len(seat_map) if isinstance(seat_map, list) else int(screen.capacity)

    booked_seats: set[str] = set()
    bookings = session.exec(
        select(Booking).where(
            Booking.showtime_id == showtime_id,
            Booking.status == "CONFIRMED",
        )
    ).all()
    for b in bookings:
        booked_seats.update(json.loads(b.seats))

    now = datetime.utcnow()
    active_holds = session.exec(
        select(SeatHold).where(
            SeatHold.showtime_id == showtime_id,
            SeatHold.status == "ACTIVE",
            SeatHold.expires_at > now,
        )
    ).all()
    held_seats: set[str] = set()
    for h in active_holds:
        try:
            held_seats.update(json.loads(h.seat_ids or "[]"))
        except (json.JSONDecodeError, TypeError):
            pass

    unavailable = booked_seats | held_seats
    return max(0, total - len(unavailable))


# ---------------------------------------------------------------------------
# Snipe execution with retry
# ---------------------------------------------------------------------------

def _attempt_snipe(
    session: Session,
    watch: SoldOutWatch,
    attempt: int = 1,
) -> dict[str, Any]:
    """Try to hold seats for the watcher. Retries up to MAX_SNIPE_RETRIES."""
    if attempt > MAX_SNIPE_RETRIES:
        return {"status": "failed", "reason": "max_retries_exceeded"}

    try:
        seat_map = get_seat_map(session, watch.showtime_id, session_key=watch.session_key)
        selected = auto_select_seats(seat_map, watch.party_size)
        if not selected:
            return {"status": "no_seats", "attempt": attempt}

        # Apply price ceiling filter if set
        if watch.price_ceiling:
            showtime = session.get(Showtime, watch.showtime_id)
            if showtime and showtime.base_price > watch.price_ceiling:
                return {"status": "price_ceiling_exceeded", "base_price": showtime.base_price}

        hold = create_seat_hold(
            session,
            showtime_id=watch.showtime_id,
            user_id=watch.user_id,
            session_key=watch.session_key,
            seat_ids=selected,
        )
        return {"status": "held", "hold_token": hold.hold_token, "seats": selected, "attempt": attempt}

    except Exception as exc:
        if attempt < MAX_SNIPE_RETRIES:
            return _attempt_snipe(session, watch, attempt + 1)
        return {"status": "failed", "reason": str(exc), "attempt": attempt}


def _notify(session: Session, user_id: int | None, title: str, message: str, metadata: dict | None = None) -> None:
    if user_id is None:
        return
    n = Notification(
        user_id=user_id,
        channel="PUSH",
        title=title,
        message=message,
        status="QUEUED",
        metadata_json=json.dumps(metadata or {}),
    )
    session.add(n)


# ---------------------------------------------------------------------------
# Snipe cycle — called by scheduler or Kafka consumer
# ---------------------------------------------------------------------------

def run_snipe_cycle(session: Session) -> dict[str, Any]:
    """
    For each ACTIVE SoldOutWatch, check if seats have freed up.
    If yes and auto_snipe=True, immediately attempt to snipe them.
    If auto_snipe=False, just notify.
    """
    now = datetime.utcnow()
    watches = session.exec(
        select(SoldOutWatch).where(
            SoldOutWatch.status == "ACTIVE",
            SoldOutWatch.created_at > now - timedelta(hours=WATCH_TTL_HOURS),
        )
    ).all()

    triggered = 0
    notified = 0
    sniped = 0
    results: list[dict] = []

    for watch in watches:
        watch.last_checked_at = now
        session.add(watch)

        available = _count_available_seats(session, watch.showtime_id)
        if available < watch.party_size:
            continue

        triggered += 1

        if not watch.auto_snipe:
            # Notify-only mode
            _notify(
                session,
                watch.user_id,
                "Seats available!",
                f"{available} seat(s) freed up for showtime #{watch.showtime_id}. Book now before they're gone!",
                {"showtime_id": watch.showtime_id, "available": available},
            )
            watch.status = "TRIGGERED"
            watch.triggered_at = now
            session.add(watch)
            notified += 1
            results.append({"watch_id": watch.id, "action": "notified", "available": available})
            continue

        # Auto-snipe
        snipe_result = _attempt_snipe(session, watch)
        if snipe_result["status"] == "held":
            watch.status = "COMPLETED"
            watch.triggered_at = now
            session.add(watch)
            sniped += 1
            _notify(
                session,
                watch.user_id,
                "Seats sniped!",
                f"I auto-reserved {watch.party_size} seat(s) for showtime #{watch.showtime_id}. "
                f"Complete your booking using token: {snipe_result['hold_token']}",
                snipe_result,
            )
            results.append({"watch_id": watch.id, "action": "sniped", **snipe_result})
        else:
            results.append({"watch_id": watch.id, "action": "snipe_failed", **snipe_result})

    session.commit()
    return {
        "watches_checked": len(watches),
        "triggered": triggered,
        "sniped": sniped,
        "notified": notified,
        "results": results,
    }
