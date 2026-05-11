from typing import Any

from sqlmodel import Session

from app.models import Booking
from app.services.checkout import persist_booking
from app.services.orchestration import run_agentic_planning
from app.services.preferences import get_or_create_memory, update_memory_with_booking


def handle_message(
    session: Session,
    user_id: int | None,
    message: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return run_agentic_planning(session, user_id, message, context=context)


def confirm_booking(
    session: Session,
    user_id: int,
    showtime_id: int,
    seats: list[str],
    *,
    hold_token: str | None = None,
    session_key: str | None = None,
) -> Booking:
    booking = persist_booking(
        session,
        user_id=user_id,
        showtime_id=showtime_id,
        seats=seats,
        hold_token=hold_token,
        session_key=session_key,
    )

    if session_key:
        memory = get_or_create_memory(session, session_key, user_id)
        update_memory_with_booking(
            session,
            memory,
            {
                "showtime_id": showtime_id,
                "seats": seats,
                "booking_id": booking.id,
            },
        )

    return booking
