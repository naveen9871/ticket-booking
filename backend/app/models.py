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


class UserPreferenceMemory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, index=True)
    session_key: str = Field(index=True)
    preference_profile: str = "{}"
    last_intent_summary: str | None = None
    last_booking_context: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, index=True)
    session_key: str = Field(index=True)
    workflow_type: str = "BOOKING"
    status: str = "CREATED"
    current_stage: str = "INTENT"
    context_json: str = "{}"
    last_error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_session_id: int = Field(index=True)
    agent_name: str
    event_type: str
    status: str
    payload_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EventPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_session_id: int = Field(index=True)
    rank: int = Field(index=True)
    title: str
    summary: str
    plan_type: str = "BALANCED"
    confidence: float = 0.0
    showtime_id: int | None = Field(default=None, index=True)
    theatre_id: int | None = Field(default=None, index=True)
    seats_json: str = "[]"
    estimated_total: float = 0.0
    rationale_json: str = "[]"
    metadata_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SeatHold(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    showtime_id: int = Field(index=True)
    user_id: int | None = Field(default=None, index=True)
    session_key: str = Field(index=True)
    seat_ids: str
    status: str = "ACTIVE"
    hold_token: str = Field(index=True, unique=True)
    expires_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserRole(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    role: str = Field(index=True)
    scope_type: str = "GLOBAL"
    scope_id: int | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TheatreProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    theatre_id: int = Field(index=True, unique=True)
    owner_user_id: int | None = Field(default=None, index=True)
    approval_status: str = "APPROVED"
    amenities: str = "[]"
    supported_formats: str = "[]"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Payment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int | None = Field(default=None, index=True)
    user_id: int = Field(index=True)
    provider: str = "DEMO_GATEWAY"
    amount: float
    currency: str = "INR"
    status: str = "INITIATED"
    idempotency_key: str = Field(index=True, unique=True)
    provider_reference: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, index=True)
    channel: str = "PUSH"
    title: str
    message: str
    status: str = "QUEUED"
    metadata_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: datetime | None = None


class ProviderIntegration(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider_code: str = Field(index=True, unique=True)
    display_name: str
    adapter_type: str = "BOOKING"
    base_url: str | None = None
    status: str = "ACTIVE"
    rate_limit_per_minute: int = 120
    circuit_state: str = "CLOSED"
    last_healthcheck_at: datetime | None = None
    config_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReleaseSubscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, index=True)
    session_key: str = Field(index=True)
    movie_title: str = Field(index=True)
    city: str = Field(index=True)
    preferred_formats: str = "[]"
    preferred_theatres: str = "[]"
    price_ceiling: float | None = None
    party_size: int = 2
    auto_reserve: bool = False
    status: str = "ACTIVE"
    last_checked_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BookingAttempt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int | None = Field(default=None, index=True)
    showtime_id: int = Field(index=True)
    user_id: int | None = Field(default=None, index=True)
    idempotency_key: str = Field(index=True)
    attempt_no: int = 1
    status: str = "STARTED"
    error_code: str | None = None
    error_message: str | None = None
    latency_ms: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    actor_user_id: int | None = Field(default=None, index=True)
    action: str = Field(index=True)
    resource_type: str
    resource_id: str | None = None
    metadata_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow)
