from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.agents.admin_agent import handle_admin_message
from app.core.deps import get_current_user
from app.db import get_session
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])

class AdminChatRequest(BaseModel):
    message: str

@router.post("/chat")
def admin_chat(payload: AdminChatRequest, session: Session = Depends(get_session), user=Depends(get_current_user)):
    if not user.is_admin:
        return {"error": "Admin access required"}
    return handle_admin_message(session, payload.message)
