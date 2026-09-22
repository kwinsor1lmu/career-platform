from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./data/app.db"
    content_path: Path = Path("content/resume.json")
    fallback_path: Path = Path("data/fallback.json")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"development", "test", "production"}:
            raise ValueError("ENVIRONMENT must be development, test, or production")
        return normalized

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "DATABASE_URL is not set or empty. Example: "
                "DATABASE_URL=sqlite:///./data/app.db"
            )
        if not normalized.startswith(("sqlite://", "postgresql://", "postgresql+psycopg://")):
            raise ValueError(
                "DATABASE_URL must use sqlite://, postgresql://, or "
                "postgresql+psycopg://"
            )
        return normalized

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        if self.environment == "production" and self.database_url.startswith("sqlite://"):
            raise ValueError("DATABASE_URL must point to PostgreSQL in production")
        return self
