from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.agents.admin_agent import handle_admin_message
from app.core.config import settings
from app.core.deps import get_current_user
from app.data.dummy_data import seed_data
from app.db import get_session
from app.models import Movie, Screen, Showtime, Theatre
from app.services.catalog import create_showtime, ensure_movie, ensure_screen, ensure_theatre, import_catalog

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminChatRequest(BaseModel):
    message: str


class MovieUpsertRequest(BaseModel):
    id: int | None = None
    title: str
    description: str = ""
    genre: str
    language: str
    duration_mins: int
    rating: float = 0.0
    poster_url: str = ""
    tags: str = ""


class TheatreUpsertRequest(BaseModel):
    id: int | None = None
    name: str
    city: str
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None


class ScreenUpsertRequest(BaseModel):
    id: int | None = None
    theatre_id: int
    name: str
    seat_map: str
    capacity: int


class ShowtimeCreateRequest(BaseModel):
    movie_id: int
    screen_id: int
    start_time: datetime
    base_price: float
    format: str = "2D"
    status: str = "SCHEDULED"


class CatalogImportRequest(BaseModel):
    movies: list[dict[str, Any]] = Field(default_factory=list)
    theatres: list[dict[str, Any]] = Field(default_factory=list)
    screens: list[dict[str, Any]] = Field(default_factory=list)
    showtimes: list[dict[str, Any]] = Field(default_factory=list)


def require_admin(user):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")


@router.post("/chat")
def admin_chat(payload: AdminChatRequest, session: Session = Depends(get_session), user=Depends(get_current_user)):
    require_admin(user)
    return handle_admin_message(session, payload.message)


@router.get("/catalog/summary")
def catalog_summary(session: Session = Depends(get_session), user=Depends(get_current_user)):
    require_admin(user)
    return {
        "movies": len(session.exec(select(Movie)).all()),
        "theatres": len(session.exec(select(Theatre)).all()),
        "screens": len(session.exec(select(Screen)).all()),
        "showtimes": len(session.exec(select(Showtime)).all()),
        "demo_seed_on_startup": settings.DEMO_SEED_ON_STARTUP,
    }


@router.post("/catalog/movies")
def upsert_movie(payload: MovieUpsertRequest, session: Session = Depends(get_session), user=Depends(get_current_user)):
    require_admin(user)
    movie = ensure_movie(session, payload.model_dump())
    return movie


@router.post("/catalog/theatres")
def upsert_theatre(payload: TheatreUpsertRequest, session: Session = Depends(get_session), user=Depends(get_current_user)):
    require_admin(user)
    theatre = ensure_theatre(session, payload.model_dump())
    return theatre


@router.post("/catalog/screens")
def upsert_screen(payload: ScreenUpsertRequest, session: Session = Depends(get_session), user=Depends(get_current_user)):
    require_admin(user)
    screen = ensure_screen(session, payload.model_dump())
    return screen


@router.post("/catalog/showtimes")
def add_showtime(payload: ShowtimeCreateRequest, session: Session = Depends(get_session), user=Depends(get_current_user)):
    require_admin(user)
    showtime = create_showtime(session, payload.model_dump())
    return showtime


@router.post("/catalog/import")
def bulk_import_catalog(payload: CatalogImportRequest, session: Session = Depends(get_session), user=Depends(get_current_user)):
    require_admin(user)
    return import_catalog(session, payload.model_dump())


@router.post("/catalog/bootstrap-demo")
def bootstrap_demo_catalog(session: Session = Depends(get_session), user=Depends(get_current_user)):
    require_admin(user)
    seed_data(session)
    return {"message": "Demo catalog seeded into the database"}
