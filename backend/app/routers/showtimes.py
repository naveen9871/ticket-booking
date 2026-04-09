from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Showtime, Screen, Theatre, Movie
from app.services.seats import get_seat_map, auto_select_seats

router = APIRouter(prefix="/showtimes", tags=["showtimes"])


@router.get("")
def list_showtimes(movie_id: int | None = None, city: str | None = None, session: Session = Depends(get_session)):
    query = select(Showtime)
    if movie_id:
        query = query.where(Showtime.movie_id == movie_id)
    showtimes = session.exec(query).all()

    if city:
        theatre_ids = [t.id for t in session.exec(select(Theatre).where(Theatre.city == city)).all()]
        screen_ids = [s.id for s in session.exec(select(Screen).where(Screen.theatre_id.in_(theatre_ids))).all()]
        showtimes = [s for s in showtimes if s.screen_id in screen_ids]

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
def showtime_seats(showtime_id: int, count: int = 2, session: Session = Depends(get_session)):
    seat_map = get_seat_map(session, showtime_id)
    suggested = auto_select_seats(seat_map, count)
    return {"seat_map": seat_map, "suggested": suggested}
