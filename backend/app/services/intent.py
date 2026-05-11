import re
from datetime import datetime, timedelta
from typing import Any

from sqlmodel import Session, select

from app.agents.llm import call_llm
from app.models import Theatre


GENRES = ["Action", "Drama", "Comedy", "Thriller", "Sci-Fi", "Romance", "Horror", "Family"]
LANGUAGES = ["Telugu", "Tamil", "Hindi", "English", "Kannada", "Malayalam"]


def _extract_budget(message: str) -> int | None:
    patterns = [
        r"under\s*(?:rs\.?|inr|₹)?\s*(\d+)",
        r"below\s*(?:rs\.?|inr|₹)?\s*(\d+)",
        r"budget\s*(?:of)?\s*(?:rs\.?|inr|₹)?\s*(\d+)",
        r"(?:rs\.?|inr|₹)\s*(\d+)",
    ]
    lowered = message.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            return int(match.group(1))
    return None


def _extract_party_size(message: str) -> int:
    match = re.search(r"(\d+)\s*(tickets?|people|seats?)", message.lower())
    if match:
        return max(int(match.group(1)), 1)
    if "date night" in message.lower():
        return 2
    if "family" in message.lower():
        return 4
    return 2


def _extract_time_hint(message: str) -> dict[str, str | None]:
    lowered = message.lower()
    if "tonight" in lowered:
        return {"time_label": "Tonight", "window": "today_evening"}
    if "this weekend" in lowered or "weekend" in lowered:
        return {"time_label": "Weekend", "window": "weekend"}
    if "friday" in lowered:
        return {"time_label": "Friday", "window": "friday"}
    if "earlier" in lowered or "afternoon" in lowered:
        return {"time_label": "Earlier", "window": "daytime"}
    return {"time_label": None, "window": None}


def _extract_city(session: Session, message: str) -> str | None:
    cities = sorted({theatre.city for theatre in session.exec(select(Theatre)).all()})
    lowered = message.lower()
    for city in cities:
        if city.lower() in lowered:
            return city
    return None


def _extract_language(message: str) -> str | None:
    lowered = message.lower()
    for language in LANGUAGES:
        if language.lower() in lowered:
            return language
    return None


def _extract_genre(message: str) -> str | None:
    lowered = message.lower()
    for genre in GENRES:
        if genre.lower() in lowered:
            return genre
    if "date night" in lowered:
        return "Romance"
    if "funny" in lowered:
        return "Comedy"
    return None


def _extract_experience_mode(message: str) -> str:
    lowered = message.lower()
    if any(token in lowered for token in ["best seats", "premium", "imax", "luxury"]):
        return "premium"
    if any(token in lowered for token in ["cheap", "budget", "under", "below"]):
        return "budget"
    if "date night" in lowered:
        return "date_night"
    return "balanced"


def _extract_intent_kind(message: str) -> str:
    lowered = message.lower()
    if any(token in lowered for token in ["book", "reserve", "buy", "confirm"]):
        return "book"
    if any(token in lowered for token in ["plan", "suggest", "recommend"]):
        return "plan"
    if any(token in lowered for token in ["showtime", "what's playing", "what is playing", "find"]):
        return "discover"
    return "discover"


def _infer_llm_summary(message: str, profile: dict[str, Any]) -> str | None:
    response = call_llm(
        [
            {
                "role": "system",
                "content": (
                    "Summarize the user's booking intent in one sentence. "
                    "Mention budget, city, timing, and preferences when present."
                ),
            },
            {
                "role": "user",
                "content": f"Message: {message}\nKnown profile: {profile}",
            },
        ]
    )
    if not response:
        return None
    choices = response.get("choices", [])
    if not choices:
        return None
    return choices[0].get("message", {}).get("content")


def parse_intent(
    session: Session,
    message: str,
    context: dict[str, Any] | None = None,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = context or {}
    profile = profile or {}
    time_hint = _extract_time_hint(message)
    city = _extract_city(session, message) or context.get("city") or (profile.get("preferred_cities") or [None])[0]
    genre = _extract_genre(message) or (profile.get("favorite_genres") or [None])[0]
    language = _extract_language(message) or (profile.get("favorite_languages") or [None])[0]
    budget_max = _extract_budget(message)
    party_size = context.get("seat_count") or _extract_party_size(message)
    experience_mode = _extract_experience_mode(message)

    if budget_max is None and experience_mode == "budget":
        budget_max = 500
    if budget_max is None and experience_mode == "premium":
        budget_max = 1500

    summary = _infer_llm_summary(message, profile)
    if not summary:
        summary = (
            f"{_extract_intent_kind(message).title()} request"
            f"{f' for {party_size} people' if party_size else ''}"
            f"{f' in {city}' if city else ''}"
            f"{f' with a {budget_max} budget' if budget_max else ''}."
        )

    now = datetime.utcnow()
    preferred_window_start = now
    preferred_window_end = now + timedelta(days=3)
    if time_hint["window"] == "today_evening":
        preferred_window_end = now + timedelta(hours=10)
    elif time_hint["window"] == "weekend":
        preferred_window_end = now + timedelta(days=7)
    elif time_hint["window"] == "friday":
        preferred_window_end = now + timedelta(days=5)

    return {
        "kind": _extract_intent_kind(message),
        "city": city,
        "genre": genre,
        "language": language,
        "budget_max": budget_max,
        "party_size": party_size,
        "experience_mode": experience_mode,
        "time_label": time_hint["time_label"],
        "time_window": time_hint["window"],
        "preferred_window_start": preferred_window_start.isoformat(),
        "preferred_window_end": preferred_window_end.isoformat(),
        "summary": summary,
        "hard_constraints": {
            "city": bool(city),
            "budget_max": bool(budget_max),
            "party_size": bool(party_size),
        },
        "soft_constraints": {
            "genre": genre,
            "language": language,
            "experience_mode": experience_mode,
        },
    }
