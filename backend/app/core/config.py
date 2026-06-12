"""
MS Learn Digest — Application Configuration
Loads all settings from environment variables.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Database ──
    DATABASE_URL: str = "postgresql://mslearn:mslearn_secret@db:5432/mslearndigest"

    # ── SMTP ──
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_EMAIL: str = ""
    SMTP_PASSWORD: str = ""

    # ── Google OAuth ──
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:5173"

    # ── Groq AI ──
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── JWT ──
    JWT_SECRET_KEY: str = "mslearndigest-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 72

    # ── App ──
    APP_NAME: str = "MS Learn Digest"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    ADMIN_ENABLED: bool = True  # Set False in production to disable /api/admin/* endpoints

    # ── Fixed timezone — all users and teams operate in IST ──
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"

    # ── MS Learn Catalog ──
    CATALOG_API_URL: str = "https://learn.microsoft.com/api/catalog/"
    # Catalog sync runs ONCE per day at this UTC hour (0–23).
    # Default: 2 AM server time so cache is warm before the first daily digests.
    CATALOG_SYNC_HOUR: int = 2
    CATALOG_SYNC_MINUTE: int = 0
    # Legacy — kept so old env files don't break; no longer drives the scheduler.
    CATALOG_SYNC_INTERVAL_MINUTES: int = 60
    ENRICHMENT_INTERVAL_MINUTES: int = 60

    # ── Team Invitations ──
    INVITATION_EXPIRY_HOURS: int = 72   # tokens expire after 3 days

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
