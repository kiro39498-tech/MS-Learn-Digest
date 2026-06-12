"""
MS Learn Digest — FastAPI Application Entry Point
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging

from app.api import api_router

# Setup structured logging
setup_logging()

from contextlib import asynccontextmanager
from app.core.scheduler import setup_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_scheduler()
    yield
    # Shutdown
    stop_scheduler()

app = FastAPI(
    title=settings.APP_NAME,
    description="API for MS Learn Digest & Team Newsletter Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "ok", "env": settings.APP_ENV}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.APP_ENV == "development" else False,
    )
