from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.agents.booking_agent import handle_message, confirm_booking
from app.core.deps import get_current_user, get_optional_user
from app.db import get_session

router = APIRouter(prefix="/assistant", tags=["assistant"])


class ChatRequest(BaseModel):
    message: str
    context: dict | None = None


class ConfirmRequest(BaseModel):
    showtime_id: int
    seats: list[str]


@router.post("/chat")
def chat(payload: ChatRequest, session: Session = Depends(get_session), user=Depends(get_optional_user)):
    user_id = user.id if user else None
    return handle_message(session, user_id, payload.message, payload.context)


@router.post("/confirm")
def confirm(payload: ConfirmRequest, session: Session = Depends(get_session), user=Depends(get_current_user)):
    booking = confirm_booking(session, user.id, payload.showtime_id, payload.seats)
    return {"booking": booking}
