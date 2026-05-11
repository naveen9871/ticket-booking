from sqlalchemy import false
from sqlmodel import Session, select

from app.models import Movie, Screen, Showtime, Theatre


def search_catalog(session: Session, query: str) -> dict:
    q = f"%{query.lower()}%"

    movies = session.exec(
        select(Movie).where(
            Movie.title.ilike(q) | Movie.genre.ilike(q) | Movie.language.ilike(q) | Movie.tags.ilike(q)
        )
    ).all()

    theatres = session.exec(
        select(Theatre).where(Theatre.name.ilike(q) | Theatre.city.ilike(q) | Theatre.address.ilike(q))
    ).all()

    movie_ids = {movie.id for movie in movies}
    theatre_ids = {theatre.id for theatre in theatres}
    screen_ids = {
        screen.id
        for screen in session.exec(select(Screen).where(Screen.theatre_id.in_(theatre_ids))).all()
    } if theatre_ids else set()

    showtimes_query = select(Showtime)
    if movie_ids and screen_ids:
        showtimes_query = showtimes_query.where(
            Showtime.movie_id.in_(movie_ids) | Showtime.screen_id.in_(screen_ids)
        )
    elif movie_ids:
        showtimes_query = showtimes_query.where(Showtime.movie_id.in_(movie_ids))
    elif screen_ids:
        showtimes_query = showtimes_query.where(Showtime.screen_id.in_(screen_ids))
    else:
        showtimes_query = showtimes_query.where(false())

    showtimes = session.exec(showtimes_query.limit(20)).all()

    return {
        "movies": movies,
        "theatres": theatres,
        "showtimes": showtimes,
    }
