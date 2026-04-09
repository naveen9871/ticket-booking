from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import init_db, get_session
from app.data.dummy_data import seed_data
from app.routers import auth, movies, theatres, showtimes, search, recommendations, bookings, assistant, admin, content

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    with get_session() as session:
        seed_data(session)


app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(movies.router, prefix=settings.API_V1_STR)
app.include_router(theatres.router, prefix=settings.API_V1_STR)
app.include_router(showtimes.router, prefix=settings.API_V1_STR)
app.include_router(search.router, prefix=settings.API_V1_STR)
app.include_router(recommendations.router, prefix=settings.API_V1_STR)
app.include_router(bookings.router, prefix=settings.API_V1_STR)
app.include_router(assistant.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(content.router, prefix=settings.API_V1_STR)
