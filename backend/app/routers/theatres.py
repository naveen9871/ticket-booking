from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Theatre

router = APIRouter(prefix="/theatres", tags=["theatres"])


@router.get("")
def list_theatres(session: Session = Depends(get_session)):
    return session.exec(select(Theatre)).all()


@router.get("/{theatre_id}")
def get_theatre(theatre_id: int, session: Session = Depends(get_session)):
    return session.exec(select(Theatre).where(Theatre.id == theatre_id)).first()
