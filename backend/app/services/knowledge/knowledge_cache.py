"""In-memory TTL cache for normalized knowledge objects."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.knowledge.knowledge_builder import KnowledgeObject


class KnowledgeCache:
    """Small process-local cache for KnowledgeObject instances."""

    def __init__(self, ttl_seconds: int = 86400) -> None:
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, tuple[datetime, KnowledgeObject]] = {}

    def make_key(
        self,
        *,
        topic: str,
        module: str,
        documentation_hash: str,
        cache_date: datetime | None = None,
    ) -> str:
        current_date = (cache_date or datetime.now(timezone.utc)).date().isoformat()
        return "|".join([
            _normalize(topic),
            _normalize(module),
            documentation_hash or "no-doc-hash",
            current_date,
        ])

    def get(self, key: str) -> KnowledgeObject | None:
        item = self._items.get(key)
        if not item:
            return None
        expires_at, knowledge = item
        if datetime.now(timezone.utc) >= expires_at:
            self._items.pop(key, None)
            return None
        return knowledge

    def set(self, key: str, knowledge: KnowledgeObject) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds)
        self._items[key] = (expires_at, knowledge)

    def clear(self) -> None:
        self._items.clear()


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())
