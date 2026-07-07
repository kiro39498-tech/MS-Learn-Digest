"""Learning-only Microsoft Learn MCP documentation enrichment."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
import hashlib
import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.learning import MCPDocumentationCache
from app.services.mcp.client import MicrosoftLearnMCPClient

logger = logging.getLogger(__name__)

_MAX_RESULTS_PER_QUERY = 5
_MAX_SUMMARY_CHARS_PER_DOC = 900
_MAX_CONTENT_CHARS_PER_DOC = 6000


@dataclass
class MCPDocumentationResult:
    """Structured MCP enrichment payload for lesson generation."""

    topic: str
    cache_date: date
    documentation_hash: str = ""
    summary: str = ""
    official_docs: list[dict[str, Any]] = field(default_factory=list)
    code_samples: list[dict[str, Any]] = field(default_factory=list)
    best_practices: list[dict[str, Any]] = field(default_factory=list)
    cache_hit: bool = False
    unavailable_reason: str | None = None
    last_updated: datetime | None = None

    @property
    def is_available(self) -> bool:
        return self.unavailable_reason is None and bool(
            self.summary or self.official_docs or self.code_samples
        )

    def to_resource_links(self) -> list[dict[str, str]]:
        """Return compact links that can be persisted and rendered in email."""
        links: list[dict[str, str]] = []
        seen: set[str] = set()
        for group in (self.official_docs, self.code_samples, self.best_practices):
            for item in group:
                url = item.get("url")
                if not url or url in seen:
                    continue
                seen.add(url)
                links.append({
                    "title": item.get("title") or url,
                    "url": url,
                    "source": "Microsoft Learn MCP",
                })
        return links

    def to_lesson_resources(self) -> list[dict[str, str]]:
        """Return LLM context resources backed by hydrated MCP documents."""
        if not self.is_available:
            return [{
                "title": "Microsoft Learn MCP",
                "url": "",
                "source": "Microsoft Learn MCP",
                "content": "Official documentation is temporarily unavailable.",
            }]

        resources = []
        if self.summary:
            resources.append({
                "title": f"Microsoft Learn MCP summary for {self.topic}",
                "url": "https://learn.microsoft.com",
                "source": "Microsoft Learn MCP",
                "content": self.summary,
            })
        for item in self.official_docs[:5]:
            resources.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source": "Microsoft Learn MCP",
                "content": item.get("content") or item.get("summary") or "",
            })
        for item in self.best_practices[:4]:
            resources.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source": "Microsoft Learn MCP best practices",
                "content": item.get("summary") or item.get("content") or "",
            })
        return resources

    def to_prompt_context(self) -> str:
        """Format MCP enrichment for the Groq lesson prompt."""
        if not self.is_available:
            return "Official documentation is temporarily unavailable."

        lines = [
            "OFFICIAL MICROSOFT LEARN MCP CONTEXT",
            f"Documentation hash: {self.documentation_hash}",
            "",
            "Summary:",
            self.summary or "No summary returned.",
            "",
            "Official documentation:",
        ]
        for doc in self.official_docs[:6]:
            lines.append(f"- {doc.get('title')} ({doc.get('url')})")
            if doc.get("summary"):
                lines.append(f"  Summary: {doc.get('summary')}")
            if doc.get("content"):
                lines.append(f"  Documentation text: {str(doc.get('content'))[:1800]}")
        if self.code_samples:
            lines.extend(["", "Code samples:"])
            for sample in self.code_samples[:6]:
                language = sample.get("language") or "sample"
                lines.append(
                    f"- {sample.get('title')} [{language}] ({sample.get('url')})"
                )
                if sample.get("summary"):
                    lines.append(f"  Summary: {sample.get('summary')}")
        if self.best_practices:
            lines.extend(["", "Best practices and architecture guidance:"])
            for item in self.best_practices[:6]:
                title = item.get("title")
                summary = item.get("summary") or item.get("content") or ""
                lines.append(f"- {title}: {summary[:350]} ({item.get('url')})")
        return "\n".join(lines)


class MicrosoftLearnDocumentationService:
    """
    Retrieves official docs, samples, and best practices through Microsoft Learn MCP.

    This service must not fetch learning paths, modules, learning progress, user
    subscriptions, or topic discovery data. Those responsibilities remain with
    the Microsoft Learn Catalog API and local learning repositories.
    """

    def __init__(
        self,
        db: Session | None = None,
        client: MicrosoftLearnMCPClient | None = None,
        cache_ttl_seconds: int | None = None,
    ) -> None:
        self.db = db
        self.client = client or MicrosoftLearnMCPClient()
        self.cache_ttl_seconds = (
            cache_ttl_seconds
            if cache_ttl_seconds is not None
            else settings.MCP_CACHE_TTL
        )

    async def search_documentation(self, topic: str) -> MCPDocumentationResult:
        """Return official documentation enrichment for a topic, cached by topic+date."""
        today = datetime.now(timezone.utc).date()
        normalized = _normalize_topic(topic)
        cached = self._get_cached(normalized, today)
        if cached:
            logger.info("MCP_CACHE | hit | topic=%s date=%s", normalized, today)
            return cached

        logger.info("MCP_CACHE | miss | topic=%s date=%s", normalized, today)
        started = datetime.now(timezone.utc)
        try:
            official_docs = await self._search_many(_documentation_queries(topic))
            code_samples = await self.get_code_samples(topic)
            best_practices = await self.get_best_practices(topic)
            summary = _build_summary(official_docs, best_practices)
            if not _has_successful_documentation(official_docs):
                raise RuntimeError("MCP returned no fetchable documentation with URL, summary, and content")
            doc_hash = _hash_payload({
                "topic": normalized,
                "summary": summary,
                "official_docs": _cache_docs(official_docs),
                "code_samples": _cache_docs(code_samples),
                "best_practices": _cache_docs(best_practices),
            })
            result = MCPDocumentationResult(
                topic=normalized,
                cache_date=today,
                documentation_hash=doc_hash,
                summary=summary,
                official_docs=_trim_docs(official_docs),
                code_samples=_trim_docs(code_samples),
                best_practices=_trim_docs(best_practices),
                cache_hit=False,
                last_updated=started,
            )
            self._save_cache(result)
            logger.info(
                "MCP | documentation | topic=%s docs=%s code_samples=%s best_practices=%s summary_len=%s hash=%s",
                normalized,
                len(result.official_docs),
                len(result.code_samples),
                len(result.best_practices),
                len(result.summary),
                result.documentation_hash,
            )
            return result
        except Exception as exc:
            logger.error(
                "MCP | documentation | unavailable | topic=%s | %s",
                normalized,
                exc,
                exc_info=True,
            )
            result = MCPDocumentationResult(
                topic=normalized,
                cache_date=today,
                documentation_hash="",
                summary="Official documentation is temporarily unavailable.",
                unavailable_reason=str(exc),
                last_updated=started,
            )
            return result

    async def fetch_documentation(self, document_id: str) -> dict[str, Any] | None:
        """
        Fetch and validate a document by id or URL through MCP.
        """
        document = await self.client.fetch(document_id=document_id, url=document_id)
        if not document:
            return None
        normalized = _normalize_reference(document)
        return normalized if _is_valid_document(normalized) else None

    async def get_code_samples(self, topic: str) -> list[dict[str, Any]]:
        """Return Microsoft Learn code sample references for a topic."""
        queries = [
            f"{topic} Python sample Microsoft Learn",
            f"{topic} C# sample Microsoft Learn",
            f"{topic} Azure CLI sample Microsoft Learn",
        ]
        results = await self._search_many(queries, purpose="code_sample")
        return [
            item for item in results
            if _looks_like_code_sample(item)
        ][:8]

    async def get_best_practices(self, topic: str) -> list[dict[str, Any]]:
        """Return best-practice, security, performance, and architecture guidance."""
        queries = [
            f"{topic} best practices Microsoft Learn",
            f"{topic} security best practices Microsoft Learn",
            f"{topic} performance tips architecture Microsoft Learn",
        ]
        return (await self._search_many(queries, purpose="best_practice"))[:8]

    async def _search_many(
        self,
        queries: list[str],
        purpose: str = "documentation",
    ) -> list[dict[str, Any]]:
        seen: set[str] = set()
        docs: list[dict[str, Any]] = []
        for query in queries:
            logger.info("MCP SEARCH | purpose=%s query=%r", purpose, query)
            results = await self.client.search(query)
            logger.info(
                "MCP SEARCH | purpose=%s query=%r returned=%s",
                purpose,
                query,
                len(results),
            )
            for item in results[:_MAX_RESULTS_PER_QUERY]:
                fetched = await self._fetch_and_validate(item, purpose=purpose)
                if not fetched:
                    logger.warning(
                        "MCP FETCH | skipped incomplete document | purpose=%s title=%r document_id=%r url=%r",
                        purpose,
                        item.get("title"),
                        item.get("document_id"),
                        item.get("url"),
                    )
                    continue
                key = fetched.get("url") or fetched.get("document_id") or fetched.get("title")
                if not key or key in seen:
                    continue
                seen.add(key)
                docs.append(fetched)
        return docs

    async def _fetch_and_validate(
        self,
        reference: dict[str, Any],
        purpose: str,
    ) -> dict[str, Any] | None:
        document_id = str(reference.get("document_id") or "")
        url = str(reference.get("url") or "")
        for attempt in range(2):
            try:
                raw = await self.client.fetch(document_id=document_id, url=url)
                logger.info("MCP FETCH | raw response before validation: %r", raw)
            except Exception as exc:
                logger.warning(
                    "MCP FETCH | failed | purpose=%s attempt=%s document_id=%r url=%r | %s",
                    purpose,
                    attempt + 1,
                    document_id,
                    url,
                    exc,
                )
                raw = None

            merged = _merge_reference_and_document(reference, raw or {})
            normalized = _normalize_reference(merged, purpose=purpose)
            if _is_valid_document(normalized):
                logger.info(
                    "MCP FETCH | retrieved | purpose=%s title=%r url=%s summary_len=%s markdown_len=%s",
                    purpose,
                    normalized.get("title"),
                    normalized.get("url"),
                    len(normalized.get("summary", "")),
                    len(normalized.get("content", "")),
                )
                return normalized

            document_id = normalized.get("document_id") or document_id
            url = normalized.get("url") or url
            logger.warning(
                "MCP FETCH | validation missing | purpose=%s attempt=%s url=%s summary_len=%s markdown_len=%s",
                purpose,
                attempt + 1,
                bool(normalized.get("url")),
                len(normalized.get("summary", "")),
                len(normalized.get("content", "")),
            )
        return None

    def _get_cached(
        self,
        topic: str,
        cache_date: date,
    ) -> MCPDocumentationResult | None:
        if not self.db:
            return None
        row = (
            self.db.query(MCPDocumentationCache)
            .filter(
                MCPDocumentationCache.topic == topic,
                MCPDocumentationCache.cache_date == cache_date,
            )
            .first()
        )
        if not row or not _is_cache_valid(row.expires_at):
            return None

        return MCPDocumentationResult(
            topic=row.topic,
            cache_date=row.cache_date,
            documentation_hash=row.documentation_hash,
            summary=row.summary,
            official_docs=row.documentation_links or [],
            code_samples=row.code_sample_links or [],
            best_practices=row.best_practices or [],
            cache_hit=True,
            unavailable_reason=row.error_message if row.source_status != "success" else None,
            last_updated=row.last_updated,
        )

    def _save_cache(self, result: MCPDocumentationResult) -> None:
        if not self.db:
            return
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=self.cache_ttl_seconds
            )
            row = (
                self.db.query(MCPDocumentationCache)
                .filter(
                    MCPDocumentationCache.topic == result.topic,
                    MCPDocumentationCache.cache_date == result.cache_date,
                )
                .first()
            )
            if not row:
                row = MCPDocumentationCache(topic=result.topic,
                                            cache_date=result.cache_date)
                self.db.add(row)

            row.documentation_hash = result.documentation_hash or _hash_payload({
                "topic": result.topic,
                "summary": result.summary,
                "unavailable": result.unavailable_reason,
            })
            row.summary = result.summary or ""
            row.documentation_links = _cache_docs(result.official_docs)
            row.code_sample_links = _cache_docs(result.code_samples)
            row.best_practices = _cache_docs(result.best_practices)
            row.source_status = "unavailable" if result.unavailable_reason else "success"
            row.error_message = result.unavailable_reason
            row.expires_at = expires_at
            row.last_updated = datetime.now(timezone.utc)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.warning("MCP_CACHE | save failed | topic=%s | %s", result.topic, exc)


def _normalize_topic(topic: str) -> str:
    return re.sub(r"\s+", " ", (topic or "").strip().lower())


def _documentation_queries(topic: str) -> list[str]:
    return [
        f"{topic} official documentation Microsoft Learn",
        f"{topic} latest documentation Microsoft Learn",
        f"{topic} architecture guidance Microsoft Learn",
    ]


def _normalize_reference(
    item: dict[str, Any],
    purpose: str = "documentation",
) -> dict[str, Any]:
    content = (
        item.get("content")
        or item.get("markdown")
        or item.get("html")
        or item.get("text")
        or item.get("summary")
        or ""
    )
    summary = item.get("summary") or item.get("description") or _summarize_text(str(content))
    url = item.get("url") or _extract_learn_url(str(content)) or ""
    document_id = item.get("document_id") or item.get("documentId") or item.get("id") or url
    language = item.get("language") or _infer_language(item)
    return {
        "title": item.get("title") or "Microsoft Learn documentation",
        "url": url,
        "document_id": document_id,
        "source": "Microsoft Learn",
        "summary": str(summary)[:_MAX_SUMMARY_CHARS_PER_DOC],
        "content": str(content)[:_MAX_CONTENT_CHARS_PER_DOC],
        "metadata": item.get("metadata") or {},
        "language": language if purpose == "code_sample" else item.get("language", ""),
    }


def _trim_docs(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_normalize_reference(doc) for doc in docs]


def _cache_docs(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "title": doc.get("title") or "Microsoft Learn documentation",
            "url": doc.get("url"),
            "summary": doc.get("summary") or "",
            "document_id": doc.get("document_id") or doc.get("url"),
            "source": doc.get("source") or "Microsoft Learn",
            "content": doc.get("content") or "",
            "metadata": doc.get("metadata") or {},
            "language": doc.get("language") or "",
        }
        for doc in docs
        if _is_valid_document(doc)
    ]


def _link_only(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "title": doc.get("title") or "Microsoft Learn documentation",
            "url": doc.get("url"),
            "summary": doc.get("summary") or "",
            "document_id": doc.get("document_id") or doc.get("url"),
            "source": doc.get("source") or "Microsoft Learn",
        }
        for doc in docs
        if doc.get("url")
    ]


def _build_summary(
    official_docs: list[dict[str, Any]],
    best_practices: list[dict[str, Any]],
) -> str:
    parts: list[str] = []
    for doc in (official_docs + best_practices)[:8]:
        title = doc.get("title") or "Microsoft Learn documentation"
        summary = _summarize_text(doc.get("content") or doc.get("summary") or "")
        if summary:
            parts.append(f"{title}: {summary}")
    return "\n".join(parts)[:5000]


def _summarize_text(text: str) -> str:
    clean = re.sub(r"\s+", " ", (text or "").strip())
    if not clean:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    summary = " ".join(sentences[:3])
    return summary[:_MAX_SUMMARY_CHARS_PER_DOC]


def _hash_payload(payload: Any) -> str:
    import json

    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_cache_valid(expires_at: datetime | None) -> bool:
    if not expires_at:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) < expires_at


def _looks_like_code_sample(item: dict[str, Any]) -> bool:
    haystack = " ".join([
        str(item.get("title", "")),
        str(item.get("url", "")),
        str(item.get("content", "")),
    ]).lower()
    return any(term in haystack for term in (
        "sample",
        "code",
        "python",
        "c#",
        "csharp",
        "cli",
        "powershell",
    ))


def _merge_reference_and_document(
    reference: dict[str, Any],
    document: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(reference)
    for key, value in (document or {}).items():
        if value not in (None, "", [], {}):
            merged[key] = value
    return merged


def _is_valid_document(doc: dict[str, Any]) -> bool:
    return bool(
        doc.get("url")
        and doc.get("summary")
        and doc.get("content")
    )


def _has_successful_documentation(docs: list[dict[str, Any]]) -> bool:
    return any(_is_valid_document(doc) for doc in docs)


def _extract_learn_url(text: str) -> str:
    match = re.search(r"https://learn\.microsoft\.com/[^\s)>\"]+", text or "")
    return match.group(0) if match else ""


def _infer_language(item: dict[str, Any]) -> str:
    haystack = " ".join([
        str(item.get("title", "")),
        str(item.get("url", "")),
        str(item.get("content", "")),
        str(item.get("summary", "")),
    ]).lower()
    if "python" in haystack:
        return "Python"
    if "c#" in haystack or "csharp" in haystack or "dotnet" in haystack:
        return "C#"
    if "azure cli" in haystack or "az " in haystack or "/cli/" in haystack:
        return "Azure CLI"
    if "powershell" in haystack:
        return "PowerShell"
    return ""
