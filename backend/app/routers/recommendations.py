from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.deps import get_current_user
from app.db import get_session
from app.services.recommendations import recommend_movies

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("")
def get_recs(session: Session = Depends(get_session), user=Depends(get_current_user)):
    return recommend_movies(session, user.id)
