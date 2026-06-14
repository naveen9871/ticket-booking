import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.deps import get_current_user
from app.db import get_session
from app.models import Booking, Movie, Notification, Screen, SeatHold, Showtime, Theatre
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
    bookings = session.exec(select(Booking).where(Booking.user_id == user.id).order_by(Booking.created_at.desc())).all()
    result = []
    for b in bookings:
        showtime = session.exec(select(Showtime).where(Showtime.id == b.showtime_id)).first()
        movie = session.exec(select(Movie).where(Movie.id == showtime.movie_id)).first() if showtime else None
        screen = session.exec(select(Screen).where(Screen.id == showtime.screen_id)).first() if showtime else None
        theatre = session.exec(select(Theatre).where(Theatre.id == screen.theatre_id)).first() if screen else None
        result.append({
            "id": b.id,
            "showtime_id": b.showtime_id,
            "seats": json.loads(b.seats) if isinstance(b.seats, str) else b.seats,
            "total_price": b.total_price,
            "status": b.status,
            "created_at": b.created_at.isoformat(),
            "movie_title": movie.title if movie else None,
            "movie_poster": movie.poster_url if movie else None,
            "theatre_name": theatre.name if theatre else None,
            "theatre_city": theatre.city if theatre else None,
            "screen_name": screen.name if screen else None,
            "showtime_format": showtime.format if showtime else None,
            "start_time": showtime.start_time.isoformat() if showtime else None,
        })
    return result


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


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: int, session: Session = Depends(get_session), user=Depends(get_current_user)):
    booking = session.exec(select(Booking).where(Booking.id == booking_id)).first()
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Already cancelled")
    if booking.status != "CONFIRMED":
        raise HTTPException(status_code=400, detail="Only confirmed bookings can be cancelled")

    booking.status = "CANCELLED"
    session.add(booking)

    # Release any confirmed seat holds tied to this booking
    holds = session.exec(
        select(SeatHold).where(
            SeatHold.showtime_id == booking.showtime_id,
            SeatHold.user_id == user.id,
            SeatHold.status == "CONFIRMED",
        )
    ).all()
    for hold in holds:
        hold.status = "RELEASED"
        hold.updated_at = datetime.utcnow()
        session.add(hold)

    # Queue a cancellation notification
    notification = Notification(
        user_id=user.id,
        channel="PUSH",
        title="Booking cancelled",
        message=f"Your booking #{booking_id} has been cancelled. Refund will be processed per policy.",
        status="QUEUED",
        metadata_json=json.dumps({"booking_id": booking_id}),
    )
    session.add(notification)
    session.commit()

    return {"booking_id": booking_id, "status": "CANCELLED", "message": "Booking cancelled successfully."}
