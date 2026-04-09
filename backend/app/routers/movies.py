from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Movie

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("")
def list_movies(session: Session = Depends(get_session)):
    return session.exec(select(Movie)).all()


@router.get("/{movie_id}")
def get_movie(movie_id: int, session: Session = Depends(get_session)):
    return session.exec(select(Movie).where(Movie.id == movie_id)).first()
