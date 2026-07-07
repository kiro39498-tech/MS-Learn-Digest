from datetime import date, datetime, timedelta, timezone

from app.services.mcp.documentation_service import (
    MCPDocumentationResult,
    MicrosoftLearnDocumentationService,
)


class FakeQuery:
    def __init__(self, db: "FakeDB") -> None:
        self.db = db

    def filter(self, *args, **kwargs) -> "FakeQuery":
        return self

    def first(self):
        return self.db.row


class FakeDB:
    def __init__(self) -> None:
        self.row = None
        self.commits = 0
        self.rollbacks = 0

    def query(self, model) -> FakeQuery:
        return FakeQuery(self)

    def add(self, row) -> None:
        self.row = row

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeClient:
    def __init__(
        self,
        results: list[dict] | None = None,
        fetched: dict | None = None,
        fail: bool = False,
    ) -> None:
        self.results = results or []
        self.fetched = fetched or {}
        self.fail = fail
        self.calls: list[str] = []
        self.fetch_calls: list[tuple[str, str]] = []

    async def search(self, query: str) -> list[dict]:
        self.calls.append(query)
        if self.fail:
            raise RuntimeError("mcp unavailable")
        return self.results

    async def fetch(self, document_id: str, url: str = "") -> dict:
        self.fetch_calls.append((document_id, url))
        if self.fail:
            raise RuntimeError("mcp unavailable")
        return self.fetched


def test_save_and_read_cache_returns_structured_result() -> None:
    db = FakeDB()
    service = MicrosoftLearnDocumentationService(db=db, cache_ttl_seconds=86400)
    result = MCPDocumentationResult(
        topic="azure functions",
        cache_date=date(2026, 7, 7),
        documentation_hash="abc123",
        summary="Official summary",
        official_docs=[{
            "title": "Docs",
            "url": "https://learn.microsoft.com/docs",
            "summary": "Docs summary",
            "content": "Hydrated documentation text.",
        }],
        code_samples=[{
            "title": "Sample",
            "url": "https://learn.microsoft.com/sample",
            "summary": "Sample summary",
            "content": "Hydrated sample text.",
            "language": "Python",
        }],
        best_practices=[{
            "title": "Best",
            "url": "https://learn.microsoft.com/best",
            "summary": "Best summary",
            "content": "Hydrated best-practice text.",
        }],
    )

    service._save_cache(result)
    cached = service._get_cached("azure functions", date(2026, 7, 7))

    assert db.commits == 1
    assert cached is not None
    assert cached.cache_hit is True
    assert cached.documentation_hash == "abc123"
    assert cached.official_docs[0]["title"] == "Docs"


def test_expired_cache_is_ignored() -> None:
    db = FakeDB()
    service = MicrosoftLearnDocumentationService(db=db)
    service._save_cache(
        MCPDocumentationResult(
            topic="azure functions",
            cache_date=date(2026, 7, 7),
            documentation_hash="abc123",
            summary="Official summary",
        )
    )
    db.row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    assert service._get_cached("azure functions", date(2026, 7, 7)) is None


async def test_search_documentation_falls_back_when_mcp_fails() -> None:
    db = FakeDB()
    service = MicrosoftLearnDocumentationService(
        db=db,
        client=FakeClient(fail=True),
        cache_ttl_seconds=86400,
    )

    result = await service.search_documentation("Azure Functions")

    assert result.is_available is False
    assert result.summary == "Official documentation is temporarily unavailable."
    assert result.unavailable_reason == "mcp unavailable"
    assert db.commits == 0


async def test_search_documentation_fetches_and_caches_hydrated_documents() -> None:
    db = FakeDB()
    client = FakeClient(
        results=[
            {
                "title": "Azure Functions docs",
                "url": "https://learn.microsoft.com/azure/azure-functions/",
                "document_id": "azure-functions",
                "content": "Search result snippet.",
            }
        ],
        fetched={
            "title": "Azure Functions docs",
            "url": "https://learn.microsoft.com/azure/azure-functions/",
            "document_id": "azure-functions",
            "summary": "Azure Functions lets you run event-driven serverless code.",
            "content": "Azure Functions is a serverless solution that lets you write less code, maintain less infrastructure, and save on costs.",
            "metadata": {"product": "azure-functions"},
        },
    )
    service = MicrosoftLearnDocumentationService(
        db=db,
        client=client,
        cache_ttl_seconds=86400,
    )

    result = await service.search_documentation("Azure Functions")

    assert result.is_available is True
    assert client.calls
    assert client.fetch_calls
    assert result.official_docs[0]["url"] == "https://learn.microsoft.com/azure/azure-functions/"
    assert result.official_docs[0]["summary"]
    assert result.official_docs[0]["content"]
    assert db.commits == 1
    assert db.row.documentation_links[0]["content"]


async def test_search_documentation_uses_cached_result() -> None:
    db = FakeDB()
    service = MicrosoftLearnDocumentationService(db=db, client=FakeClient())
    today = datetime.now(timezone.utc).date()
    service._save_cache(
        MCPDocumentationResult(
            topic="azure functions",
            cache_date=today,
            documentation_hash="abc123",
            summary="Cached summary",
        )
    )

    result = await service.search_documentation("Azure Functions")

    assert result.cache_hit is True
    assert result.summary == "Cached summary"
