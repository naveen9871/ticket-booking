import json
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models import UserPreferenceMemory


def _default_profile(session_key: str) -> dict[str, Any]:
    return {
        "session_key": session_key,
        "favorite_genres": [],
        "favorite_languages": [],
        "preferred_cities": [],
        "price_sensitivity": "balanced",
        "seat_bias": "center",
        "party_sizes": [],
        "recent_queries": [],
    }


def get_or_create_memory(session: Session, session_key: str, user_id: int | None = None) -> UserPreferenceMemory:
    statement = select(UserPreferenceMemory).where(UserPreferenceMemory.session_key == session_key)
    memory = session.exec(statement).first()
    if memory:
        if user_id and memory.user_id is None:
            memory.user_id = user_id
            memory.updated_at = datetime.utcnow()
            session.add(memory)
            session.commit()
            session.refresh(memory)
        return memory

    memory = UserPreferenceMemory(
        user_id=user_id,
        session_key=session_key,
        preference_profile=json.dumps(_default_profile(session_key)),
    )
    session.add(memory)
    session.commit()
    session.refresh(memory)
    return memory


def load_profile(memory: UserPreferenceMemory) -> dict[str, Any]:
    try:
        return json.loads(memory.preference_profile or "{}")
    except json.JSONDecodeError:
        return _default_profile(memory.session_key)


def update_memory_from_intent(
    session: Session,
    memory: UserPreferenceMemory,
    intent: dict[str, Any],
    raw_message: str,
) -> UserPreferenceMemory:
    profile = load_profile(memory)

    genre = intent.get("genre")
    language = intent.get("language")
    city = intent.get("city")
    party_size = intent.get("party_size")
    budget = intent.get("budget_max")

    if genre and genre not in profile["favorite_genres"]:
        profile["favorite_genres"].append(genre)
    if language and language not in profile["favorite_languages"]:
        profile["favorite_languages"].append(language)
    if city and city not in profile["preferred_cities"]:
        profile["preferred_cities"].append(city)
    if party_size and party_size not in profile["party_sizes"]:
        profile["party_sizes"].append(party_size)

    if budget:
        if budget <= 400:
            profile["price_sensitivity"] = "high"
        elif budget >= 900:
            profile["price_sensitivity"] = "low"
        else:
            profile["price_sensitivity"] = "balanced"

    profile["recent_queries"] = [raw_message, *profile["recent_queries"]][:5]

    memory.preference_profile = json.dumps(profile)
    memory.last_intent_summary = intent.get("summary")
    memory.updated_at = datetime.utcnow()
    session.add(memory)
    session.commit()
    session.refresh(memory)
    return memory


def update_memory_with_booking(session: Session, memory: UserPreferenceMemory, booking_context: dict[str, Any]) -> None:
    memory.last_booking_context = json.dumps(booking_context)
    memory.updated_at = datetime.utcnow()
    session.add(memory)
    session.commit()
