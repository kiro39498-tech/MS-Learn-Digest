"""
MS Learn Digest — Structured Logging
"""

import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
    )
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Quiet noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
