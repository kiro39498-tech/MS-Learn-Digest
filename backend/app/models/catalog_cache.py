"""
CatalogCache — Lightweight metadata cache for Microsoft Learn content.

Populated by the hourly catalog sync job.
No AI enrichment. No change tracking. No scraping.
Contains only what the MS Learn Catalog API returns directly.

Used by digest generation to:
  1. Query items modified within the user's frequency window.
  2. Filter by products/subjects overlap against user topic subscriptions.
  3. Build the Groq prompt payload.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.core.database import Base


class CatalogCache(Base):
    __tablename__ = "catalog_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uid = Column(String(500), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    content_type = Column(String(100), nullable=False)   # 'module' | 'learningPath'
    summary = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    products_json = Column(JSONB, nullable=False, default=list)   # ["azure", ...]
    subjects_json = Column(JSONB, nullable=False, default=list)   # ["ai", ...]

    # Timezone-aware timestamp from the Catalog API ("2026-03-13T17:10:00+00:00")
    last_modified = Column(DateTime(timezone=True), nullable=True, index=True)

    # Set to now() on every upsert — tells us how fresh this row is
    last_synced_at = Column(DateTime(timezone=True), nullable=False)
