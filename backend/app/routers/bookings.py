import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.deps import get_current_user
from app.db import get_session
from app.models import Booking, Showtime
from app.services.pricing import compute_dynamic_price

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("")
def list_bookings(session: Session = Depends(get_session), user=Depends(get_current_user)):
    return session.exec(select(Booking).where(Booking.user_id == user.id)).all()


@router.post("")
def create_booking(showtime_id: int, seats: list[str], session: Session = Depends(get_session), user=Depends(get_current_user)):
    showtime = session.exec(select(Showtime).where(Showtime.id == showtime_id)).first()
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    pricing = compute_dynamic_price(session, showtime.id, showtime.base_price)
    total = pricing["price"] * len(seats)
    booking = Booking(user_id=user.id, showtime_id=showtime_id, seats=json.dumps(seats), total_price=total)
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking
