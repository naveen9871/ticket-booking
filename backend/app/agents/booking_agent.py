import json
import re
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.agents.llm import call_llm, extract_tool_call
from app.models import Movie, Showtime, Booking, Screen, Theatre
from app.services.search import search_catalog
from app.services.recommendations import recommend_movies
from app.services.seats import get_seat_map, auto_select_seats
from app.services.pricing import compute_dynamic_price


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_catalog",
            "description": "Search movies and theatres",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_movies",
            "description": "Recommend movies for a user",
            "parameters": {
                "type": "object",
                "properties": {"user_id": {"type": "integer"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "auto_select_seats",
            "description": "Auto select best seats",
            "parameters": {
                "type": "object",
                "properties": {"showtime_id": {"type": "integer"}, "count": {"type": "integer"}},
                "required": ["showtime_id", "count"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_dynamic_price",
            "description": "Compute price for showtime",
            "parameters": {
                "type": "object",
                "properties": {"showtime_id": {"type": "integer"}},
                "required": ["showtime_id"],
            },
        },
    },
]


SYSTEM_PROMPT = """
You are Ticketly's premium booking assistant. Your goal is to make ticket booking effortless and cinematic.
- Be concise but helpful.
- If the user is looking for a movie, use 'search_catalog'.
- If they want to book, suggest the best seats using 'auto_select_seats' and check the 'compute_dynamic_price'.
- Always confirm the city and showtime before final booking.
- Use a friendly, modern tone.
"""

MAX_SHOWTIMES = 12

def _fallback_intent(message: str) -> str:
    m = message.lower()
    if m.strip() in {"hi", "hello", "hey", "yo", "hola"}:
        return "greet"
    if "recommend" in m or "suggest" in m:
        return "recommend"
    if "what movies" in m or "movies are playing" in m or "now showing" in m:
        return "list_movies"
    if "search" in m or "find" in m:
        return "search"
    if "showtime" in m or "show times" in m or "theatre" in m or "theater" in m:
        return "showtimes"
    if "nearby" in m or "near by" in m or "near me" in m:
        return "nearby"
    if "book" in m or "tickets" in m:
        return "book"
    if "confirm" in m or "go ahead" in m or "book it" in m:
        return "confirm"
    if "price" in m or "cost" in m:
        return "price"
    return "chat"


def _match_movie(session: Session, message: str) -> Movie | None:
    m = message.lower()
    if "bahubali" in m:
        m = m.replace("bahubali", "baahubali")
    if len(m.strip()) < 3:
        return None
    tokens = [t for t in re.split(r"\\W+", m) if len(t) >= 4]
    movies = session.exec(select(Movie)).all()
    for movie in movies:
        title = movie.title.lower()
        if title in m and len(title) >= 4:
            return movie
        if any(token in title for token in tokens):
            return movie
    return None


def _extract_city(session: Session, message: str) -> str | None:
    cities = {t.city.lower() for t in session.exec(select(Theatre)).all()}
    m = message.lower()
    for city in cities:
        if city in m:
            return city.title()
    return None


def _extract_seat_count(message: str) -> int | None:
    match = re.search(r"(\\d+)\\s*(tickets?|seats?)", message.lower())
    if match:
        return int(match.group(1))
    return None


def _pick_best_showtime(showtimes: list[Showtime]) -> Showtime | None:
    if not showtimes:
        return None
    return sorted(showtimes, key=lambda s: s.start_time)[0]


def _showtime_context(session: Session, showtime: Showtime) -> dict[str, Any]:
    screen = session.exec(select(Screen).where(Screen.id == showtime.screen_id)).first()
    theatre = None
    if screen:
        theatre = session.exec(select(Theatre).where(Theatre.id == screen.theatre_id)).first()
    movie = session.exec(select(Movie).where(Movie.id == showtime.movie_id)).first()
    return {
        "showtime_id": showtime.id,
        "movie": {"id": movie.id, "title": movie.title} if movie else None,
        "theatre": {"id": theatre.id, "name": theatre.name, "city": theatre.city, "address": theatre.address} if theatre else None,
        "screen": {"id": screen.id, "name": screen.name} if screen else None,
        "start_time": showtime.start_time.isoformat(),
        "format": showtime.format,
        "base_price": showtime.base_price,
    }


def handle_message(session: Session, user_id: int | None, message: str, context: dict | None = None) -> dict[str, Any]:
    context = context or {}
    lower = message.lower()
    city = _extract_city(session, message) or context.get("city")
    seat_count = _extract_seat_count(message) or context.get("seat_count", 2)
    context.update({"city": city, "seat_count": seat_count})

    if ("theatre" in lower or "theater" in lower) and context.get("showtime_id"):
        showtime = session.exec(select(Showtime).where(Showtime.id == context["showtime_id"])).first()
        if showtime:
            details = _showtime_context(session, showtime)
            theatre = details.get("theatre")
            if theatre:
                return {
                    "type": "message",
                    "message": f"Theatre: {theatre['name']}, {theatre['city']} — {theatre['address']}.",
                }

    llm = call_llm(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        tools=TOOLS,
    )
    tool_call = extract_tool_call(llm) if llm else None

    if tool_call:
        name, args = tool_call
        if name == "search_catalog":
            results = search_catalog(session, args["query"])
            return {"type": "search_results", "data": results}
        if name == "recommend_movies":
            movies = recommend_movies(session, user_id)
            return {"type": "recommendations", "data": movies}
        if name == "auto_select_seats":
            seat_map = get_seat_map(session, args["showtime_id"])
            seats = auto_select_seats(seat_map, args["count"])
            return {"type": "seat_selection", "data": {"seats": seats, "seat_map": seat_map}}
        if name == "compute_dynamic_price":
            showtime = session.exec(select(Showtime).where(Showtime.id == args["showtime_id"])).first()
            if not showtime:
                return {"type": "error", "message": "Showtime not found"}
            pricing = compute_dynamic_price(session, showtime.id, showtime.base_price)
            return {"type": "pricing", "data": pricing}

    intent = _fallback_intent(message)
    if intent == "recommend":
        movies = recommend_movies(session, user_id)
        return {"type": "recommendations", "data": movies}

    if intent == "greet":
        return {"type": "message", "message": "Hi! Tell me a movie or city, and I can show showtimes."}

    if intent == "search":
        results = search_catalog(session, message)
        return {"type": "search_results", "data": results}

    if intent == "list_movies":
        movies = session.exec(select(Movie)).all()
        return {"type": "movie_list", "data": movies}

    if intent == "nearby":
        city = context.get("city")
        if not city:
            return {"type": "message", "message": "Which city are you in? I can show nearby movies."}
        showtimes = session.exec(select(Showtime)).all()
        enriched = []
        for show in showtimes:
            details = _showtime_context(session, show)
            theatre = details.get("theatre") or {}
            if theatre.get("city") != city:
                continue
            movie = details.get("movie") or {}
            enriched.append(
                {
                    "showtime_id": show.id,
                    "movie_title": movie.get("title"),
                    "theatre_name": theatre.get("name"),
                    "city": theatre.get("city"),
                    "start_time": show.start_time.isoformat(),
                    "format": show.format,
                    "price": show.base_price,
                }
            )
        return {"type": "showtimes", "data": enriched}

    if intent == "showtimes":
        movie = _match_movie(session, message)
        if not movie:
            return {"type": "message", "message": "Which movie do you want showtimes for?"}
        showtimes = session.exec(select(Showtime).where(Showtime.movie_id == movie.id)).all()
        if city:
            filtered = []
            for s in showtimes:
                details = _showtime_context(session, s)
                if (details.get("theatre") or {}).get("city") == city:
                    filtered.append(s)
            showtimes = filtered
        enriched = []
        for show in showtimes[:MAX_SHOWTIMES]:
            details = _showtime_context(session, show)
            theatre = details.get("theatre") or {}
            enriched.append(
                {
                    "showtime_id": show.id,
                    "movie_title": movie.title,
                    "theatre_name": theatre.get("name"),
                    "city": theatre.get("city"),
                    "start_time": show.start_time.isoformat(),
                    "format": show.format,
                    "price": show.base_price,
                }
            )
        return {"type": "showtimes", "data": enriched}

    if intent == "price" and context.get("showtime_id"):
        showtime = session.exec(select(Showtime).where(Showtime.id == context["showtime_id"])).first()
        if showtime:
            pricing = compute_dynamic_price(session, showtime.id, showtime.base_price)
            return {"type": "pricing", "data": pricing}

    if intent == "book":
        movie = _match_movie(session, message)
        if not movie:
            return {"type": "message", "message": "Which movie do you want to book?"}
        if not city:
            return {"type": "message", "message": f"Got it. Which city for {movie.title}?"}
        showtime = None
        if movie:
            showtimes = session.exec(select(Showtime).where(Showtime.movie_id == movie.id)).all()
            if city:
                filtered = []
                for s in showtimes:
                    details = _showtime_context(session, s)
                    if (details.get("theatre") or {}).get("city") == city:
                        filtered.append(s)
                showtimes = filtered
            showtime = _pick_best_showtime(showtimes)
        if not showtime:
            return {"type": "error", "message": "No showtimes available"}
        seat_map = get_seat_map(session, showtime.id)
        seats = auto_select_seats(seat_map, seat_count)
        pricing = compute_dynamic_price(session, showtime.id, showtime.base_price)
        details = _showtime_context(session, showtime)
        return {
            "type": "booking_proposal",
            "data": {
                "showtime_id": showtime.id,
                "seats": seats,
                "price": pricing,
                "details": details,
            },
        }

    if intent == "confirm" and context.get("showtime_id") and user_id:
        seats = context.get("seats") or []
        if not seats:
            seat_map = get_seat_map(session, context["showtime_id"])
            seats = auto_select_seats(seat_map, seat_count)
        booking = confirm_booking(session, user_id, context["showtime_id"], seats)
        return {"type": "booking_confirmed", "data": {"booking_id": booking.id}}

    showtime_response = _maybe_return_showtimes(session, message)
    if showtime_response:
        return showtime_response

    return {
        "type": "message",
        "message": "Tell me the movie, city, and time you prefer. I can also auto-pick the best seats.",
    }


def _maybe_return_showtimes(session: Session, message: str) -> dict[str, Any] | None:
    movie = _match_movie(session, message)
    if not movie:
        return None
    showtimes = session.exec(select(Showtime).where(Showtime.movie_id == movie.id)).all()
    enriched = []
    for show in showtimes[:MAX_SHOWTIMES]:
        details = _showtime_context(session, show)
        theatre = details.get("theatre") or {}
        enriched.append(
            {
                "showtime_id": show.id,
                "movie_title": movie.title,
                "theatre_name": theatre.get("name"),
                "city": theatre.get("city"),
                "start_time": show.start_time.isoformat(),
                "format": show.format,
                "price": show.base_price,
            }
        )
    return {"type": "showtimes", "data": enriched}


def confirm_booking(session: Session, user_id: int, showtime_id: int, seats: list[str]) -> Booking:
    showtime = session.exec(select(Showtime).where(Showtime.id == showtime_id)).first()
    if not showtime:
        raise ValueError("Showtime not found")
    pricing = compute_dynamic_price(session, showtime.id, showtime.base_price)
    total = pricing["price"] * len(seats)
    booking = Booking(user_id=user_id, showtime_id=showtime_id, seats=json.dumps(seats), total_price=total)
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking
