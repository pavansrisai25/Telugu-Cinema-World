"""Application settings, loaded from environment variables / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # SQLite locally; on AWS this becomes a PostgreSQL RDS URL.
    database_url: str = "sqlite:///./telugu_cinema.db"
    tmdb_api_key: str = ""  # used from Phase 2
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()