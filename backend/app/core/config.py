from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Google identity scopes plus read-only Gmail and Calendar. The frontend requests the
# same list in src/config/google.ts.
GOOGLE_OAUTH_SCOPES = (
    "openid",
    "profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
)


class Settings(BaseSettings):
    """All configuration comes from environment variables or backend/.env.

    Never read os.environ anywhere else.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Inbox Copilot API"
    version: str = "0.1.0"
    log_level: str = "INFO"

    google_client_id: str
    google_client_secret: str
    token_encryption_key: str
    anthropic_api_key: str

    database_url: str = "sqlite:///./app.db"
    session_ttl_days: int = 7
    cookie_secure: bool = False
    # Empty = same-origin deployment (Vite proxy in dev, reverse proxy in prod).
    cors_origins: list[str] = []

    # Weather (Open-Meteo, no API key). Used when a question names no place.
    weather_home_location: str = "Berlin"
    weather_timezone: str = "Europe/Berlin"
    weather_units: Literal["metric", "imperial"] = "metric"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # required fields come from the environment
