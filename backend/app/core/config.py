import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env path relative to this file (works regardless of working directory)
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"

# Pre-populate os.environ from .env so pydantic-settings picks it up correctly
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _, _v = _line.partition("=")
        _k = _k.strip()
        _v = _v.strip().strip('"').strip("'")
        # Override if not set or set to empty string
        if _k and not os.environ.get(_k):
            os.environ[_k] = _v


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Ticketly"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    SECRET_KEY: str = "change-me-in-production-with-a-long-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    DATABASE_URL: str = "sqlite:///./ticketly.db"

    # CORS — comma-separated list of allowed origins
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://arosai.in,https://www.arosai.in"

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None

    OTP_SENDER_NAME: str = "Ticketly"
    OTP_TTL_SECONDS: int = 300

    # LLM provider selection: "claude" | "gemini" | "openai"
    LLM_PROVIDER: str = "claude"

    # Anthropic / Claude
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"

    # Google Gemini
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # OpenAI
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    REDIS_URL: str = "redis://localhost:6379/0"
    SEAT_HOLD_TTL_SECONDS: int = 180
    DEMO_SEED_ON_STARTUP: bool = False

    # Razorpay
    RAZORPAY_KEY_ID: str = "rzp_test_T1S4DLu3XvrFRf"
    RAZORPAY_KEY_SECRET: str = "cLkCtFhWIz0u4AYOmMOQUrhO"

    # Email (SendGrid)
    SENDGRID_API_KEY: str | None = None
    EMAIL_FROM: str = "noreply@ticketly.in"
    EMAIL_FROM_NAME: str = "Ticketly"

    # Rate limiting
    RATE_LIMIT_SEAT_HOLD: str = "10/minute"
    RATE_LIMIT_BOOKING: str = "20/minute"

    # Showtime cache TTL in seconds
    SHOWTIME_CACHE_TTL: int = 60


settings = Settings()
