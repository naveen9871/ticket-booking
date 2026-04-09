from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.services.search import search_catalog

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(query: str, session: Session = Depends(get_session)):
    return search_catalog(session, query)
