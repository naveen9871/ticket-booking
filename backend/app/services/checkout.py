import json

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Booking, Showtime
from app.services.pricing import compute_dynamic_price
from app.services.seats import confirm_hold, create_seat_hold


def persist_booking(
    session: Session,
    *,
    user_id: int,
    showtime_id: int,
    seats: list[str],
    hold_token: str | None = None,
    session_key: str | None = None,
) -> Booking:
    showtime = session.exec(select(Showtime).where(Showtime.id == showtime_id)).first()
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")

    if hold_token:
        hold = confirm_hold(session, hold_token, user_id=user_id)
        seats = json.loads(hold.seat_ids)
    elif session_key:
        hold = create_seat_hold(
            session,
            showtime_id,
            seats,
            session_key=session_key,
            user_id=user_id,
            ttl_seconds=30,
        )
        hold.status = "CONFIRMED"
        session.add(hold)
        session.commit()

    pricing = compute_dynamic_price(session, showtime.id, showtime.base_price)
    total = pricing["price"] * len(seats)
    booking = Booking(user_id=user_id, showtime_id=showtime_id, seats=json.dumps(seats), total_price=total)
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking
