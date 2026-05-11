from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    PROJECT_NAME: str = "Ticketly"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    DATABASE_URL: str = "sqlite:///./ticketly.db"

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None

    OTP_SENDER_NAME: str = "Ticketly"
    OTP_TTL_SECONDS: int = 300

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    LLM_PROVIDER: str = "gemini" # 'openai' or 'gemini'

    REDIS_URL: str = "redis://localhost:6379/0"
    SEAT_HOLD_TTL_SECONDS: int = 180
    DEMO_SEED_ON_STARTUP: bool = False


settings = Settings()
