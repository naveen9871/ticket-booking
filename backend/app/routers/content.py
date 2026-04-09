from fastapi import APIRouter

from app.agents.content_agent import generate_blurb

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/blurb")
def blurb(title: str, genre: str):
    return generate_blurb(title, genre)
