from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Movie, Screen, Showtime, Theatre


def ensure_movie(session: Session, payload: dict[str, Any]) -> Movie:
    movie = None
    if payload.get("id"):
        movie = session.get(Movie, payload["id"])
    if not movie:
        movie = session.exec(select(Movie).where(Movie.title == payload["title"])).first()

    if movie is None:
        movie = Movie(
            title=payload["title"],
            description=payload.get("description", ""),
            genre=payload.get("genre", "Unknown"),
            language=payload.get("language", "Unknown"),
            duration_mins=payload.get("duration_mins", 0),
            rating=payload.get("rating", 0.0),
            poster_url=payload.get("poster_url", ""),
            tags=payload.get("tags", ""),
        )
    else:
        movie.description = payload.get("description", movie.description)
        movie.genre = payload.get("genre", movie.genre)
        movie.language = payload.get("language", movie.language)
        movie.duration_mins = payload.get("duration_mins", movie.duration_mins)
        movie.rating = payload.get("rating", movie.rating)
        movie.poster_url = payload.get("poster_url", movie.poster_url)
        movie.tags = payload.get("tags", movie.tags)

    session.add(movie)
    session.commit()
    session.refresh(movie)
    return movie


def ensure_theatre(session: Session, payload: dict[str, Any]) -> Theatre:
    theatre = None
    if payload.get("id"):
        theatre = session.get(Theatre, payload["id"])
    if not theatre:
        theatre = session.exec(
            select(Theatre).where(Theatre.name == payload["name"], Theatre.city == payload["city"])
        ).first()

    if theatre is None:
        theatre = Theatre(
            name=payload["name"],
            city=payload["city"],
            address=payload.get("address", ""),
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
        )
    else:
        theatre.address = payload.get("address", theatre.address)
        theatre.latitude = payload.get("latitude", theatre.latitude)
        theatre.longitude = payload.get("longitude", theatre.longitude)

    session.add(theatre)
    session.commit()
    session.refresh(theatre)
    return theatre


def ensure_screen(session: Session, payload: dict[str, Any]) -> Screen:
    theatre = session.get(Theatre, payload["theatre_id"])
    if not theatre:
        raise HTTPException(status_code=404, detail="Theatre not found")

    screen = None
    if payload.get("id"):
        screen = session.get(Screen, payload["id"])
    if not screen:
        screen = session.exec(
            select(Screen).where(Screen.theatre_id == payload["theatre_id"], Screen.name == payload["name"])
        ).first()

    if screen is None:
        screen = Screen(
            theatre_id=payload["theatre_id"],
            name=payload["name"],
            seat_map=payload["seat_map"],
            capacity=payload["capacity"],
        )
    else:
        screen.seat_map = payload.get("seat_map", screen.seat_map)
        screen.capacity = payload.get("capacity", screen.capacity)

    session.add(screen)
    session.commit()
    session.refresh(screen)
    return screen


def create_showtime(session: Session, payload: dict[str, Any]) -> Showtime:
    movie = session.get(Movie, payload["movie_id"])
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    screen = session.get(Screen, payload["screen_id"])
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")

    showtime = Showtime(
        movie_id=payload["movie_id"],
        screen_id=payload["screen_id"],
        start_time=payload["start_time"],
        base_price=payload["base_price"],
        format=payload.get("format", "2D"),
        status=payload.get("status", "SCHEDULED"),
    )
    session.add(showtime)
    session.commit()
    session.refresh(showtime)
    return showtime


def import_catalog(session: Session, payload: dict[str, Any]) -> dict[str, int]:
    movie_lookup: dict[str, Movie] = {}
    theatre_lookup: dict[str, Theatre] = {}
    screen_lookup: dict[str, Screen] = {}

    for movie_payload in payload.get("movies", []):
        movie = ensure_movie(session, movie_payload)
        movie_lookup[movie_payload.get("external_id") or movie.title] = movie

    for theatre_payload in payload.get("theatres", []):
        theatre = ensure_theatre(session, theatre_payload)
        theatre_lookup[theatre_payload.get("external_id") or f"{theatre.name}:{theatre.city}"] = theatre

    for screen_payload in payload.get("screens", []):
        theatre_ref = screen_payload.get("theatre_external_id")
        if theatre_ref and not screen_payload.get("theatre_id"):
            theatre = theatre_lookup.get(theatre_ref)
            if not theatre:
                raise HTTPException(status_code=404, detail=f"Theatre external id not found: {theatre_ref}")
            screen_payload["theatre_id"] = theatre.id
        screen = ensure_screen(session, screen_payload)
        screen_lookup[screen_payload.get("external_id") or f"{screen.theatre_id}:{screen.name}"] = screen

    imported_showtimes = 0
    for showtime_payload in payload.get("showtimes", []):
        movie_ref = showtime_payload.get("movie_external_id")
        if movie_ref and not showtime_payload.get("movie_id"):
            movie = movie_lookup.get(movie_ref)
            if not movie:
                raise HTTPException(status_code=404, detail=f"Movie external id not found: {movie_ref}")
            showtime_payload["movie_id"] = movie.id

        screen_ref = showtime_payload.get("screen_external_id")
        if screen_ref and not showtime_payload.get("screen_id"):
            screen = screen_lookup.get(screen_ref)
            if not screen:
                raise HTTPException(status_code=404, detail=f"Screen external id not found: {screen_ref}")
            showtime_payload["screen_id"] = screen.id

        if isinstance(showtime_payload.get("start_time"), str):
            showtime_payload["start_time"] = datetime.fromisoformat(showtime_payload["start_time"])

        create_showtime(session, showtime_payload)
        imported_showtimes += 1

    return {
        "movies": len(payload.get("movies", [])),
        "theatres": len(payload.get("theatres", [])),
        "screens": len(payload.get("screens", [])),
        "showtimes": imported_showtimes,
    }
