"""
MS Learn Catalog API Client

Fetches modules and learningPaths from the MS Learn Catalog API
using separate filtered requests per content type.

Filtering by ?type= reduces response size dramatically:
  - All types (unfiltered): ~30-50 MB, 2-5 minutes
  - modules only:           ~8-12 MB, 15-30 seconds
  - learningPaths only:     ~2-4 MB,  5-10 seconds

This keeps each request well within timeout limits and avoids
the large memory spike from a single 50 MB JSON parse.
"""

import httpx
import logging
from typing import Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

# Separate timeout for catalog fetches — each filtered request is
# much smaller than the full unfiltered catalog.
_CATALOG_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)


class CatalogClient:
    def __init__(self):
        self.base_url = settings.CATALOG_API_URL.rstrip("/")
        self.client = httpx.AsyncClient(timeout=_CATALOG_TIMEOUT)

    async def fetch_by_type(self, content_type: str, locale: str = "en-us") -> List[Dict[str, Any]]:
        """
        Fetch only one content type from the catalog API.

        content_type: 'modules' | 'learningPaths'

        The ?type= filter reduces the payload from ~40 MB (all types)
        to ~8 MB (modules) or ~3 MB (learningPaths), which is far
        faster and more reliable.
        """
        url = f"{self.base_url}?type={content_type}&locale={locale}"
        logger.info(f"CATALOG | fetching {content_type} from {url}")
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            items = data.get(content_type, [])
            logger.info(f"CATALOG | {content_type}: {len(items)} items fetched")
            return items
        except httpx.ReadTimeout:
            logger.error(
                f"CATALOG | ReadTimeout fetching {content_type} — "
                f"consider increasing CATALOG_SYNC_INTERVAL_MINUTES"
            )
            raise
        except httpx.HTTPError as exc:
            logger.error(f"CATALOG | HTTP error fetching {content_type}: {exc}")
            raise
        except Exception as exc:
            logger.error(f"CATALOG | Unexpected error fetching {content_type}: {exc}")
            raise

    # Keep fetch_catalog() as a compatibility shim — it now uses
    # filtered requests internally instead of one giant unfiltered call.
    async def fetch_catalog(self) -> Dict[str, Any]:
        """
        Fetch all supported content types and return as a combined dict.
        Kept for backward compatibility with CatalogSyncService.
        """
        modules = await self.fetch_by_type("modules")
        learning_paths = await self.fetch_by_type("learningPaths")
        return {
            "modules": modules,
            "learningPaths": learning_paths,
        }

    async def close(self):
        await self.client.aclose()

    @staticmethod
    def extract_items(catalog_data: Dict[str, Any], item_type: str = "modules") -> List[Dict[str, Any]]:
        return catalog_data.get(item_type, [])
