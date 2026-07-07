from app.services.knowledge.knowledge_builder import KnowledgeBuilder
from app.services.knowledge.knowledge_cache import KnowledgeCache
from app.services.lesson.diagram_generator import DiagramGenerator
from app.services.lesson.exercise_generator import ExerciseGenerator
from app.services.lesson.interview_generator import InterviewGenerator
from app.services.lesson.lesson_coordinator import LessonCoordinator
from app.services.lesson.lesson_generator import LessonContentGenerator
from app.services.lesson.lesson_merger import LessonMerger
from app.services.lesson.quality_reviewer import QualityReviewer
from app.services.lesson.quiz_generator import QuizGenerator
from app.services.lesson.summary_generator import SummaryGenerator


def _knowledge():
    return KnowledgeBuilder().build(
        topic_name="Azure",
        module_title="Azure Functions",
        sequence_number=1,
        total_modules=10,
        learning_objectives=["Understand serverless compute"],
        keywords=["functions", "serverless"],
        difficulty_level="beginner",
        resources=[
            {
                "title": "Azure Functions documentation",
                "url": "https://learn.microsoft.com/azure/azure-functions/",
                "source": "Microsoft Learn MCP",
                "summary": "Azure Functions is a serverless compute service.",
                "content": "Azure Functions lets you run event-driven code without managing infrastructure. Python sample code is available.",
            },
            {
                "title": "Azure Functions best practices",
                "url": "https://learn.microsoft.com/azure/azure-functions/functions-best-practices",
                "source": "Microsoft Learn MCP",
                "content": "Use best practices for performance, reliability, and security.",
            },
        ],
        mcp_context="OFFICIAL MICROSOFT LEARN MCP CONTEXT",
    )


def test_knowledge_builder_normalizes_official_sources() -> None:
    knowledge = _knowledge()

    assert knowledge.topic_name == "Azure"
    assert knowledge.official_urls
    assert knowledge.documentation_summary
    assert knowledge.documentation_hash
    assert knowledge.source_status == "available"
    assert knowledge.code_samples
    assert knowledge.best_practices


def test_knowledge_cache_round_trips_by_key() -> None:
    cache = KnowledgeCache(ttl_seconds=86400)
    knowledge = _knowledge()
    key = cache.make_key(
        topic=knowledge.topic_name,
        module=knowledge.module_title,
        documentation_hash=knowledge.documentation_hash,
    )

    cache.set(key, knowledge)

    assert cache.get(key) is knowledge


async def test_each_generator_has_independent_fallback() -> None:
    knowledge = _knowledge()
    generators = [
        LessonContentGenerator(),
        QuizGenerator(),
        ExerciseGenerator(),
        InterviewGenerator(),
        SummaryGenerator(),
        DiagramGenerator(),
    ]

    outputs = [await generator.generate(knowledge) for generator in generators]

    assert outputs[0]["today_goal"]
    assert outputs[1]["quiz"]
    assert outputs[2]["practical_exercise"]
    assert outputs[3]["questions"]["beginner"]
    assert outputs[4]["summary"]
    assert outputs[5]["architecture_diagram"]


def test_merger_and_quality_reviewer_keep_legacy_contract() -> None:
    knowledge = _knowledge()
    merged = LessonMerger().merge(
        knowledge=knowledge,
        lesson=LessonContentGenerator().fallback(knowledge),
        quiz=QuizGenerator().fallback(knowledge),
        exercise=ExerciseGenerator().fallback(knowledge),
        interview=InterviewGenerator().fallback(knowledge),
        summary=SummaryGenerator().fallback(knowledge),
        diagram=DiagramGenerator().fallback(knowledge),
        generation_time_ms=10,
        model="test-model",
    )
    reviewed = QualityReviewer().review(merged)

    assert reviewed["today_goal"]
    assert reviewed["quiz"]
    assert reviewed["questions"]
    assert reviewed["practical_exercise"]
    assert reviewed["hands_on_activity"]
    assert reviewed["lesson"]
    assert reviewed["metadata"]["generator_version"] == "2.0.0"


async def test_coordinator_runs_without_client_and_returns_legacy_shape() -> None:
    result = await LessonCoordinator(client=None, model="test-model").generate(
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
    assert content["module_title"] == "Azure Functions"
    assert content["official_documentation_status"] == "temporarily_unavailable"
    assert "metadata" in content
    assert result["resource_links"] == []
