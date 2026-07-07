from app.core.config import settings
from app.services.learning.lesson_generator import (
    LessonGeneratorService,
    _build_official_context,
)


def test_build_official_context_prioritizes_mcp_context() -> None:
    context = _build_official_context(
        resources=[
            {
                "title": "Supplemental",
                "url": "https://example.test/resource",
                "content": "Supplemental context",
            }
        ],
        mcp_context="OFFICIAL MICROSOFT LEARN MCP CONTEXT\nOfficial docs",
    )

    assert context.startswith("OFFICIAL MICROSOFT LEARN MCP CONTEXT")
    assert "SUPPLEMENTAL DISCOVERED RESOURCES" in context
    assert "Supplemental context" in context


async def test_generate_lesson_returns_fallback_without_groq_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    service = LessonGeneratorService()

    result = await service.generate_lesson(
        topic_name="Azure",
        module_title="Azure Functions",
        sequence_number=1,
        total_modules=10,
        learning_objectives=["Understand serverless compute"],
        keywords=["functions"],
        difficulty_level="beginner",
        resources=[],
        mcp_context="Official documentation is temporarily unavailable.",
    )

    content = result["content_json"]
    assert service.client is None
    assert content["module_title"] == "Azure Functions"
    assert content["official_documentation_status"] == "temporarily_unavailable"
    assert "best_practices" in content
