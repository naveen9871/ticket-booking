from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.deps import get_current_user
from app.db import get_session
from app.models import Booking
from app.services.checkout import persist_booking
from app.services.tickets import build_ticket

router = APIRouter(prefix="/bookings", tags=["bookings"])


class BookingCreateRequest(BaseModel):
    showtime_id: int
    seats: list[str]
    hold_token: str | None = None
    session_key: str | None = None


@router.get("")
def list_bookings(session: Session = Depends(get_session), user=Depends(get_current_user)):
    return session.exec(select(Booking).where(Booking.user_id == user.id)).all()


@router.post("")
def create_booking(
    payload: BookingCreateRequest,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    booking = persist_booking(
        session,
        user_id=user.id,
        showtime_id=payload.showtime_id,
        seats=payload.seats,
        hold_token=payload.hold_token,
        session_key=payload.session_key,
    )
    return booking


@router.get("/{booking_id}/ticket")
def get_ticket(booking_id: int, session: Session = Depends(get_session), user=Depends(get_current_user)):
    booking = session.exec(select(Booking).where(Booking.id == booking_id)).first()
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    ticket = build_ticket(session, booking_id)
    return ticket
