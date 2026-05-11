import json
from datetime import datetime, timedelta
from secrets import token_urlsafe
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Booking, Screen, SeatHold, Showtime


DEFAULT_HOLD_TTL_SECONDS = getattr(settings, "SEAT_HOLD_TTL_SECONDS", 180)


def release_expired_holds(session: Session) -> None:
    now = datetime.utcnow()
    expired = session.exec(
        select(SeatHold).where(SeatHold.status == "ACTIVE", SeatHold.expires_at < now)
    ).all()
    for hold in expired:
        hold.status = "EXPIRED"
        hold.updated_at = now
        session.add(hold)
    if expired:
        session.commit()


def _load_screen_seat_map(session: Session, showtime_id: int) -> list[list[dict[str, Any]]]:
    showtime = session.exec(select(Showtime).where(Showtime.id == showtime_id)).first()
    if not showtime:
        return []
    screen = session.exec(select(Screen).where(Screen.id == showtime.screen_id)).first()
    if not screen:
        return []
    return json.loads(screen.seat_map)


def _booked_seats(session: Session, showtime_id: int) -> set[str]:
    bookings = session.exec(select(Booking).where(Booking.showtime_id == showtime_id)).all()
    booked: set[str] = set()
    for booking in bookings:
        booked.update(json.loads(booking.seats))
    return booked


def _active_holds(session: Session, showtime_id: int) -> list[SeatHold]:
    release_expired_holds(session)
    now = datetime.utcnow()
    return session.exec(
        select(SeatHold).where(
            SeatHold.showtime_id == showtime_id,
            SeatHold.status == "ACTIVE",
            SeatHold.expires_at >= now,
        )
    ).all()


def get_seat_map(
    session: Session,
    showtime_id: int,
    session_key: str | None = None,
    hold_token: str | None = None,
) -> list[list[dict[str, Any]]]:
    seat_map = _load_screen_seat_map(session, showtime_id)
    if not seat_map:
        return []

    booked = _booked_seats(session, showtime_id)
    holds = _active_holds(session, showtime_id)

    held_by_you: set[str] = set()
    held_by_others: set[str] = set()
    for hold in holds:
        seat_ids = set(json.loads(hold.seat_ids))
        if hold.hold_token == hold_token or (session_key and hold.session_key == session_key):
            held_by_you.update(seat_ids)
        else:
            held_by_others.update(seat_ids)

    for row in seat_map:
        for seat in row:
            if seat["id"] in booked:
                seat["status"] = "BOOKED"
            elif seat["id"] in held_by_you:
                seat["status"] = "HELD_BY_YOU"
            elif seat["id"] in held_by_others:
                seat["status"] = "HELD"
            else:
                seat["status"] = "AVAILABLE"
    return seat_map


def auto_select_seats(seat_map: list[list[dict[str, Any]]], count: int) -> list[str]:
    if count <= 0 or not seat_map:
        return []

    num_rows = len(seat_map)
    middle_row = num_rows // 2
    best_seats: list[str] = []
    min_distance_from_center = float("inf")

    for r_idx, row in enumerate(seat_map):
        num_cols = len(row)
        middle_col = num_cols // 2
        for idx in range(len(row) - count + 1):
            block = row[idx : idx + count]
            if all(seat["status"] in {"AVAILABLE", "HELD_BY_YOU"} for seat in block):
                block_center = idx + (count / 2)
                score = abs(r_idx - middle_row) + abs(block_center - middle_col)
                if score < min_distance_from_center:
                    min_distance_from_center = score
                    best_seats = [seat["id"] for seat in block]
    return best_seats


def create_seat_hold(
    session: Session,
    showtime_id: int,
    seats: list[str],
    *,
    session_key: str,
    user_id: int | None = None,
    ttl_seconds: int = DEFAULT_HOLD_TTL_SECONDS,
) -> SeatHold:
    if not seats:
        raise HTTPException(status_code=400, detail="No seats selected")

    seat_map = get_seat_map(session, showtime_id, session_key=session_key)
    seat_lookup = {seat["id"]: seat for row in seat_map for seat in row}
    unavailable = [
        seat_id
        for seat_id in seats
        if seat_id not in seat_lookup or seat_lookup[seat_id]["status"] in {"BOOKED", "HELD"}
    ]
    if unavailable:
        raise HTTPException(status_code=409, detail=f"Seats unavailable: {', '.join(unavailable)}")

    now = datetime.utcnow()
    existing = session.exec(
        select(SeatHold).where(
            SeatHold.showtime_id == showtime_id,
            SeatHold.session_key == session_key,
            SeatHold.status == "ACTIVE",
        )
    ).all()
    for hold in existing:
        hold.status = "RELEASED"
        hold.updated_at = now
        session.add(hold)

    hold = SeatHold(
        showtime_id=showtime_id,
        user_id=user_id,
        session_key=session_key,
        seat_ids=json.dumps(seats),
        hold_token=token_urlsafe(18),
        expires_at=now + timedelta(seconds=ttl_seconds),
        created_at=now,
        updated_at=now,
    )
    session.add(hold)
    session.commit()
    session.refresh(hold)
    return hold


def get_hold(session: Session, hold_token: str) -> SeatHold | None:
    release_expired_holds(session)
    return session.exec(select(SeatHold).where(SeatHold.hold_token == hold_token)).first()


def confirm_hold(session: Session, hold_token: str, user_id: int | None = None) -> SeatHold:
    hold = get_hold(session, hold_token)
    if not hold or hold.status != "ACTIVE":
        raise HTTPException(status_code=404, detail="Seat hold not found or expired")
    if user_id and hold.user_id is None:
        hold.user_id = user_id
    hold.status = "CONFIRMED"
    hold.updated_at = datetime.utcnow()
    session.add(hold)
    session.commit()
    session.refresh(hold)
    return hold


def release_hold(session: Session, hold_token: str) -> None:
    hold = get_hold(session, hold_token)
    if not hold:
        return
    hold.status = "RELEASED"
    hold.updated_at = datetime.utcnow()
    session.add(hold)
    session.commit()
