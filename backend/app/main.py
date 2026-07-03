"""
MS Learn Digest — FastAPI Application Entry Point
=================================================
CORS origins are driven entirely by the ALLOWED_ORIGINS environment variable
(comma-separated list).  This means:

  Local development  → ALLOWED_ORIGINS=http://localhost:5173
  Production (Render)→ ALLOWED_ORIGINS=https://ms-learn-digest-git-learnings-kiro9898.vercel.app

No source code change is ever needed when switching environments.
See app/core/config.py for the full resolution logic.
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api import api_router

# Initialise structured logging before anything else so startup logs are captured.
setup_logging()

import logging
logger = logging.getLogger(__name__)

from app.core.scheduler import setup_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the APScheduler on boot and stop it cleanly on shutdown."""
    setup_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    description="API for MS Learn Digest & Team Newsletter Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api")

# ── CORS ─────────────────────────────────────────────────────────────────────
# settings.cors_origins parses the ALLOWED_ORIGINS env var (comma-separated).
# Falls back to FRONTEND_URL, then to localhost for local-only dev.
# Never requires a code change between environments.
_cors_origins = settings.cors_origins
logger.info(f"CORS allow_origins={_cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint — used by Render and Docker Compose health probes."""
    return {
        "status": "ok",
        "env": settings.APP_ENV,
        "frontend_url": settings.FRONTEND_URL,
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=(settings.APP_ENV == "development"),
    )
