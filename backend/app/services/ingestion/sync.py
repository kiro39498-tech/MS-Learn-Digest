"""
CatalogSyncService — Lightweight metadata cache sync.

Fetches modules and learningPaths separately using filtered API requests,
then upserts uid/title/url/content_type/summary/products/subjects/last_modified
into catalog_cache.

Explicitly NOT responsible for:
  - AI enrichment
  - Change detection
  - Scraping
  - Any other processing
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.catalog_cache import CatalogCache
from app.services.ingestion.catalog_client import CatalogClient

logger = logging.getLogger(__name__)

_VALID_URL_PREFIX = "https://learn.microsoft.com"


def _parse_ts(raw: Optional[str]) -> Optional[datetime]:
    """Parse a catalog ISO-8601 timestamp to a timezone-aware datetime."""
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return None


class SyncResult:
    def __init__(self):
        self.fetched = 0
        self.upserted = 0
        self.invalid_urls = 0

    def to_dict(self):
        return {
            "fetched": self.fetched,
            "upserted": self.upserted,
            "invalid_urls": self.invalid_urls,
        }


class CatalogSyncService:
    def __init__(self, db: Session):
        self.db = db
        self.client = CatalogClient()

    async def sync_catalog(self) -> SyncResult:
        """
        Fetch modules and learningPaths separately (filtered requests are
        much faster than one unfiltered 40 MB catalog call), then upsert
        into catalog_cache.
        """
        total = SyncResult()
        now = datetime.now(timezone.utc)

        for content_type, api_type in [
            ("module", "modules"),
            ("learningPath", "learningPaths"),
        ]:
            logger.info(f"SYNC | fetching {api_type}...")
            try:
                items = await self.client.fetch_by_type(api_type)
            except Exception as exc:
                logger.error(f"SYNC | FETCH_FAILED | {api_type}: {exc}", exc_info=True)
                await self.client.close()
                raise

            result = self._upsert_items(items, content_type, now)
            total.fetched += result.fetched
            total.upserted += result.upserted
            total.invalid_urls += result.invalid_urls

            logger.info(
                f"SYNC | {api_type} done | "
                f"fetched={result.fetched} upserted={result.upserted} "
                f"invalid_urls={result.invalid_urls}"
            )

        await self.client.close()
        logger.info(
            f"SYNC | COMPLETE | fetched={total.fetched} upserted={total.upserted}"
        )
        return total

    def _upsert_items(
        self,
        items: List[Dict[str, Any]],
        content_type: str,
        now: datetime,
    ) -> SyncResult:
        result = SyncResult()
        result.fetched = len(items)
        batch = 0

        for item in items:
            uid = (item.get("uid") or "").strip()
            if not uid:
                continue

            url = item.get("url") or ""
            if not url.startswith(_VALID_URL_PREFIX):
                logger.warning(f"SYNC | INVALID_URL | uid={uid} url={url!r}")
                result.invalid_urls += 1
                # Still cache it so it shows up in diagnostics

            stmt = pg_insert(CatalogCache).values(
                uid=uid,
                title=item.get("title") or "Unknown Title",
                url=url,
                content_type=content_type,
                summary=item.get("summary") or None,
                duration_minutes=item.get("duration_in_minutes") or None,
                products_json=item.get("products") or [],
                subjects_json=item.get("subjects") or [],
                last_modified=_parse_ts(item.get("last_modified")),
                last_synced_at=now,
            ).on_conflict_do_update(
                index_elements=["uid"],
                set_={
                    "title":            pg_insert(CatalogCache).excluded.title,
                    "url":              pg_insert(CatalogCache).excluded.url,
                    "summary":          pg_insert(CatalogCache).excluded.summary,
                    "duration_minutes": pg_insert(CatalogCache).excluded.duration_minutes,
                    "products_json":    pg_insert(CatalogCache).excluded.products_json,
                    "subjects_json":    pg_insert(CatalogCache).excluded.subjects_json,
                    "last_modified":    pg_insert(CatalogCache).excluded.last_modified,
                    "last_synced_at":   pg_insert(CatalogCache).excluded.last_synced_at,
                },
            )
            self.db.execute(stmt)
            result.upserted += 1
            batch += 1

            if batch % 500 == 0:
                self.db.commit()
                logger.info(f"SYNC | {content_type} progress: {batch} upserted...")

        self.db.commit()
        return result
