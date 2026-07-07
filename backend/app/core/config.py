"""
MS Learn Digest — Application Configuration
============================================
All settings are loaded exclusively from environment variables (or a .env file
for local development).  No URL, credential, or environment-specific value is
ever hard-coded here.

Environment resolution
----------------------
Local development:  values come from the project-root .env file (auto-discovered
                    three directory levels above this file).
Production (Render): values come from Render's "Environment Variables" panel.
                    The .env file is not present on Render, which is correct —
                    pydantic-settings falls back gracefully to env vars.

Key variables
-------------
FRONTEND_URL        — The canonical origin of the React frontend.
                      Local:       http://localhost:5173
                      Production:  https://ms-learn-digest-git-learnings-kiro9898.vercel.app

ALLOWED_ORIGINS     — Comma-separated list of origins allowed by CORS.
                      Supports multiple origins so both localhost and production
                      can be whitelisted simultaneously without code changes.
                      Local:       http://localhost:5173
                      Production:  https://ms-learn-digest-git-learnings-kiro9898.vercel.app
                      Both:        http://localhost:5173,https://ms-learn-digest-git-learnings-kiro9898.vercel.app

GOOGLE_REDIRECT_URI — The OAuth callback URL registered in Google Cloud Console.
                      Local:       http://localhost:8000/auth/google/callback
                      Production:  https://ms-learn-digest.onrender.com/auth/google/callback

Note: the frontend sends its own window.location.origin-based redirect_uri at
runtime, so GOOGLE_REDIRECT_URI on the backend is only used as a fallback in
auth_service.py. Both values must be registered in Google Cloud Console.
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

# Resolve .env path relative to this file so it works regardless of cwd.
# config.py lives at:  <project>/backend/app/core/config.py
# .env lives at:       <project>/.env  (three levels up)
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """
    Application settings — every value must come from environment variables.
    Defaults are only provided for non-secret, non-URL settings that are safe
    to fall back on (e.g. algorithm names, feature flags, timeouts).
    Any URL or secret MUST be set explicitly in the environment.
    """

    # ── Database ──────────────────────────────────────────────────────────
    # Local default points at the Docker Compose db service.
    # On Render, set DATABASE_URL to your Neon/Render PostgreSQL connection string.
    DATABASE_URL: str = "postgresql://mslearn:mslearn_secret@db:5432/mslearndigest"

    # ── SMTP ──────────────────────────────────────────────────────────────
    # Gmail SMTP settings. Use a Gmail App Password, not your account password.
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_EMAIL: str = ""
    SMTP_PASSWORD: str = ""

    # ── Google OAuth ──────────────────────────────────────────────────────
    # GOOGLE_REDIRECT_URI must be set per environment:
    #   Local:      http://localhost:8000/auth/google/callback
    #   Production: https://ms-learn-digest.onrender.com/auth/google/callback
    # Both must be registered as "Authorised Redirect URIs" in Google Cloud Console.
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""       # Required — no localhost default in code
    FRONTEND_URL: str = ""              # Required — no localhost default in code

    # ── CORS ──────────────────────────────────────────────────────────────
    # Comma-separated list of allowed frontend origins.
    # Example (local):       ALLOWED_ORIGINS=http://localhost:5173
    # Example (production):  ALLOWED_ORIGINS=https://ms-learn-digest-git-learnings-kiro9898.vercel.app
    # Example (both):        ALLOWED_ORIGINS=http://localhost:5173,https://ms-learn-digest-git-learnings-kiro9898.vercel.app
    # Falls back to FRONTEND_URL when not explicitly set.
    ALLOWED_ORIGINS: str = ""

    # ── Groq AI ───────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── JWT ───────────────────────────────────────────────────────────────
    # JWT_SECRET_KEY must be a long, random string in production.
    JWT_SECRET_KEY: str = ""            # Required — no insecure default
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 72

    # ── App ───────────────────────────────────────────────────────────────
    APP_NAME: str = "MS Learn Digest"
    APP_ENV: str = "development"        # Set to "production" on Render
    LOG_LEVEL: str = "INFO"
    ADMIN_ENABLED: bool = True          # Set False in production to lock /api/admin/*

    # ── Fixed timezone — all users and teams operate in IST ───────────────
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"

    # ── MS Learn Catalog ──────────────────────────────────────────────────
    CATALOG_API_URL: str = "https://learn.microsoft.com/api/catalog/"
    CATALOG_SYNC_HOUR: int = 2          # UTC hour for daily catalog sync (0–23)
    CATALOG_SYNC_MINUTE: int = 0
    CATALOG_SYNC_INTERVAL_MINUTES: int = 60     # Legacy — no longer drives scheduler
    ENRICHMENT_INTERVAL_MINUTES: int = 60

    # ── Microsoft Learn MCP ───────────────────────────────────────────────
    # Used only to enrich Learning lessons with official documentation context.
    # The Catalog API remains the source for paths, modules, progress, and topics.
    MCP_SERVER_URL: str = "https://learn.microsoft.com/api/mcp"
    MCP_TIMEOUT: float = 10.0
    MCP_RETRIES: int = 2
    MCP_CACHE_TTL: int = 86400          # seconds; default is 24 hours

    # ── Team Invitations ──────────────────────────────────────────────────
    INVITATION_EXPIRY_HOURS: int = 72   # Invitation tokens expire after 3 days

    # ── Email Login ───────────────────────────────────────────────────────
    EMAIL_LOGIN_TOKEN_EXPIRY_MINUTES: int = 15  # Magic-link expires in 15 minutes
    EMAIL_LOGIN_MAX_ATTEMPTS_PER_HOUR: int = 5  # Rate limit per email address

    # ── Computed property: parsed CORS origins list ───────────────────────

    @property
    def cors_origins(self) -> List[str]:
        """
        Returns the list of origins FastAPI CORS middleware should allow.

        Resolution order:
          1. ALLOWED_ORIGINS env var (comma-separated, highest priority — use this
             in production to allow multiple origins without code changes).
          2. FRONTEND_URL env var (single-origin fallback for simple setups).
          3. http://localhost:5173 (last-resort local dev fallback — never reached
             in production because ALLOWED_ORIGINS or FRONTEND_URL must be set).
        """
        if self.ALLOWED_ORIGINS:
            return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        if self.FRONTEND_URL:
            return [self.FRONTEND_URL]
        # Should never reach here in production — ALLOWED_ORIGINS or FRONTEND_URL must be set.
        return ["http://localhost:5173"]

    class Config:
        env_file = str(_ENV_FILE)
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# ── Startup validation ────────────────────────────────────────────────────────
# Fail loudly on boot if critical variables are missing, rather than silently
# producing broken behaviour at runtime.
_REQUIRED = {
    "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET,
    "GOOGLE_REDIRECT_URI": settings.GOOGLE_REDIRECT_URI,
    "FRONTEND_URL": settings.FRONTEND_URL,
    "JWT_SECRET_KEY": settings.JWT_SECRET_KEY,
    "GROQ_API_KEY": settings.GROQ_API_KEY,
}

_missing = [k for k, v in _REQUIRED.items() if not v]
if _missing:
    import warnings
    warnings.warn(
        f"[MS Learn Digest] Missing required environment variables: {', '.join(_missing)}. "
        "The application may not function correctly. "
        "Copy .env.example to .env and fill in all values.",
        RuntimeWarning,
        stacklevel=2,
    )
