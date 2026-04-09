from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: Optional[str] = Field(default=None, index=True, unique=True)
    phone: Optional[str] = Field(default=None, index=True, unique=True)
    full_name: str | None = None
    hashed_password: str | None = None
    oauth_provider: str | None = None
    oauth_subject: str | None = None
    otp_code: str | None = None
    otp_expires_at: datetime | None = None
    genre_preferences: str | None = None  # Comma separated
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Movie(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    genre: str
    language: str
    duration_mins: int
    rating: float
    poster_url: str
    tags: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Theatre(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    city: str
    address: str
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Screen(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    theatre_id: int = Field(index=True)
    name: str
    seat_map: str
    capacity: int


class Showtime(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    movie_id: int = Field(index=True)
    screen_id: int = Field(index=True)
    start_time: datetime
    base_price: float
    format: str
    status: str = "SCHEDULED"


class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    showtime_id: int = Field(index=True)
    seats: str
    total_price: float
    status: str = "CONFIRMED"
    created_at: datetime = Field(default_factory=datetime.utcnow)
