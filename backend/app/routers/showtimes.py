import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import Movie, Screen, Theatre, Showtime
from app.services.pricing import compute_dynamic_price
from app.services.seats import create_seat_hold, get_hold, get_seat_map, auto_select_seats

router = APIRouter(prefix="/showtimes", tags=["showtimes"])


class HoldRequest(BaseModel):
    seats: list[str]
    session_key: str
    user_id: int | None = None


@router.get("")
def list_showtimes(movie_id: int | None = None, city: str | None = None, session: Session = Depends(get_session)):
    query = select(Showtime)
    if movie_id:
        query = query.where(Showtime.movie_id == movie_id)
    showtimes = session.exec(query).all()

    if city:
        theatre_ids = [theatre.id for theatre in session.exec(select(Theatre).where(Theatre.city == city)).all()]
        screen_ids = [screen.id for screen in session.exec(select(Screen).where(Screen.theatre_id.in_(theatre_ids))).all()]
        showtimes = [showtime for showtime in showtimes if showtime.screen_id in screen_ids]

    enriched = []
    for show in showtimes:
        screen = session.exec(select(Screen).where(Screen.id == show.screen_id)).first()
        theatre = session.exec(select(Theatre).where(Theatre.id == screen.theatre_id)).first() if screen else None
        movie = session.exec(select(Movie).where(Movie.id == show.movie_id)).first()
        enriched.append(
            {
                "id": show.id,
                "movie_id": show.movie_id,
                "movie_title": movie.title if movie else None,
                "screen_id": show.screen_id,
                "screen_name": screen.name if screen else None,
                "theatre_id": theatre.id if theatre else None,
                "theatre_name": theatre.name if theatre else None,
                "city": theatre.city if theatre else None,
                "start_time": show.start_time,
                "base_price": show.base_price,
                "format": show.format,
                "status": show.status,
            }
        )
    return enriched


@router.get("/{showtime_id}/seats")
def showtime_seats(
    showtime_id: int,
    count: int = 2,
    session_key: str | None = None,
    hold_token: str | None = None,
    session: Session = Depends(get_session),
):
    seat_map = get_seat_map(session, showtime_id, session_key=session_key, hold_token=hold_token)
    suggested = auto_select_seats(seat_map, count)
    return {"seat_map": seat_map, "suggested": suggested}


@router.post("/{showtime_id}/holds")
def create_hold(showtime_id: int, payload: HoldRequest, session: Session = Depends(get_session)):
    hold = create_seat_hold(
        session,
        showtime_id,
        payload.seats,
        session_key=payload.session_key,
        user_id=payload.user_id,
    )
    return {
        "hold_id": hold.id,
        "hold_token": hold.hold_token,
        "expires_at": hold.expires_at.isoformat(),
        "seats": json.loads(hold.seat_ids),
    }


@router.get("/{showtime_id}/pricing")
def showtime_pricing(showtime_id: int, hold_token: str | None = None, session: Session = Depends(get_session)):
    showtime = session.exec(select(Showtime).where(Showtime.id == showtime_id)).first()
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")

    pricing = compute_dynamic_price(session, showtime_id, showtime.base_price)
    seat_count = 0
    if hold_token:
        hold = get_hold(session, hold_token)
        if hold and hold.status == "ACTIVE":
            seat_count = len(json.loads(hold.seat_ids))

    return {
        **pricing,
        "seat_count": seat_count,
        "total": round(pricing["price"] * seat_count, 2) if seat_count else None,
    }
