"""
config.py – Centralised settings loaded from environment variables.

Pydantic-Settings reads from a .env file (or real env vars) and validates
every value at startup, giving fail-fast behaviour before any DB connection.
"""

from functools import lru_cache
from typing import List

from pydantic import AnyUrl, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "Varanbook Matrimonial SaaS"
    APP_ENV: str = Field("development", pattern="^(development|staging|production)$")
    DEBUG: bool = False
    SECRET_KEY: str  # must be set in env; no default for security

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: PostgresDsn          # e.g. postgresql+asyncpg://user:pass@host/db
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── AWS ───────────────────────────────────────────────────────────────────
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "varanbook-media"
    S3_PRESIGNED_URL_EXPIRY: int = 3600  # seconds
    SQS_NOTIFICATION_QUEUE_URL: str = ""

    # ── Tenant resolution ─────────────────────────────────────────────────────
    # Header or subdomain strategy; header is simpler for API-first.
    TENANT_ID_HEADER: str = "X-Tenant-ID"

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Email / SMTP ──────────────────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@example.com"
    APP_FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        """Ensure the async driver prefix is present."""
        if "asyncpg" not in v and "postgresql" in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


@lru_cache()  # singleton – created once per worker process
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
