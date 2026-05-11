from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models import Movie, Screen, Showtime, Theatre


def enrich_showtime(session: Session, showtime: Showtime) -> dict[str, Any]:
    screen = session.exec(select(Screen).where(Screen.id == showtime.screen_id)).first()
    theatre = session.exec(select(Theatre).where(Theatre.id == screen.theatre_id)).first() if screen else None
    movie = session.exec(select(Movie).where(Movie.id == showtime.movie_id)).first()
    return {
        "id": showtime.id,
        "movie_id": showtime.movie_id,
        "movie_title": movie.title if movie else None,
        "movie_genre": movie.genre if movie else None,
        "movie_language": movie.language if movie else None,
        "movie_rating": movie.rating if movie else None,
        "screen_id": showtime.screen_id,
        "screen_name": screen.name if screen else None,
        "theatre_id": theatre.id if theatre else None,
        "theatre_name": theatre.name if theatre else None,
        "city": theatre.city if theatre else None,
        "address": theatre.address if theatre else None,
        "start_time": showtime.start_time.isoformat(),
        "base_price": showtime.base_price,
        "format": showtime.format,
        "status": showtime.status,
    }


def _matches_time_window(start_time: datetime, time_window: str | None) -> bool:
    if not time_window:
        return True
    weekday = start_time.weekday()
    if time_window == "today_evening":
        return start_time.date() == datetime.utcnow().date() and start_time.hour >= 17
    if time_window == "weekend":
        return weekday >= 4
    if time_window == "friday":
        return weekday == 4
    if time_window == "daytime":
        return start_time.hour < 18
    return True


def discover_showtimes(session: Session, intent: dict[str, Any], limit: int = 24) -> list[dict[str, Any]]:
    query = select(Showtime).where(Showtime.status == "SCHEDULED")
    showtimes = session.exec(query).all()

    candidates: list[dict[str, Any]] = []
    for showtime in showtimes:
        enriched = enrich_showtime(session, showtime)

        if intent.get("city") and enriched["city"] != intent["city"]:
            continue
        if intent.get("genre") and enriched["movie_genre"] != intent["genre"]:
            continue
        if intent.get("language") and enriched["movie_language"] != intent["language"]:
            continue
        if intent.get("budget_max") and enriched["base_price"] * intent.get("party_size", 1) > intent["budget_max"]:
            continue
        if not _matches_time_window(showtime.start_time, intent.get("time_window")):
            continue

        score = float(enriched["movie_rating"] or 0)
        if enriched["format"] == "IMAX":
            score += 0.35
        if intent.get("experience_mode") == "budget":
            score += max(0, 500 - enriched["base_price"]) / 500
        if intent.get("experience_mode") == "premium":
            score += enriched["base_price"] / 500
        if intent.get("city") and enriched["city"] == intent["city"]:
            score += 0.2

        enriched["discovery_score"] = round(score, 3)
        candidates.append(enriched)

    candidates.sort(key=lambda item: (-item["discovery_score"], item["start_time"]))
    return candidates[:limit]
