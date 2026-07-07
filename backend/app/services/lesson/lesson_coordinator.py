"""Coordinator for the modular lesson generation pipeline."""

from __future__ import annotations

from typing import Any
import asyncio
import hashlib
import json
import logging
import time

from app.services.knowledge.knowledge_builder import KnowledgeBuilder, KnowledgeObject
from app.services.knowledge.knowledge_cache import KnowledgeCache
from app.services.lesson.diagram_generator import DiagramGenerator
from app.services.lesson.exercise_generator import ExerciseGenerator
from app.services.lesson.interview_generator import InterviewGenerator
from app.services.lesson.lesson_generator import LessonContentGenerator
from app.services.lesson.lesson_merger import LessonMerger
from app.services.lesson.quality_reviewer import QualityReviewer
from app.services.lesson.quiz_generator import QuizGenerator
from app.services.lesson.summary_generator import SummaryGenerator

logger = logging.getLogger(__name__)


class LessonCoordinator:
    """Orchestrates knowledge, focused generators, merge, and review."""

    def __init__(
        self,
        *,
        client: Any = None,
        model: str = "",
        knowledge_builder: KnowledgeBuilder | None = None,
        knowledge_cache: KnowledgeCache | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.knowledge_builder = knowledge_builder or KnowledgeBuilder()
        self.knowledge_cache = knowledge_cache or KnowledgeCache()
        self.merger = LessonMerger()
        self.reviewer = QualityReviewer()

    async def generate(self, **kwargs: Any) -> dict[str, Any]:
        total_started = time.monotonic()
        knowledge = self._load_knowledge(**kwargs)
        resource_links = [
            {"title": item.get("title", ""), "url": item.get("url", ""), "source": item.get("source", "Microsoft Learn")}
            for item in knowledge.official_documentation
            if item.get("url")
        ]

        generators = {
            "lesson": LessonContentGenerator(self.client, self.model),
            "quiz": QuizGenerator(self.client, self.model),
            "exercise": ExerciseGenerator(self.client, self.model),
            "interview": InterviewGenerator(self.client, self.model),
            "summary": SummaryGenerator(self.client, self.model),
            "diagram": DiagramGenerator(self.client, self.model),
        }
        results = await asyncio.gather(
            *(generator.generate(knowledge) for generator in generators.values()),
            return_exceptions=True,
        )
        section_outputs = {
            name: self._coerce_section(name, result, knowledge)
            for name, result in zip(generators.keys(), results)
        }
        generation_time_ms = int((time.monotonic() - total_started) * 1000)
        merged = self.merger.merge(
            knowledge=knowledge,
            lesson=section_outputs["lesson"],
            quiz=section_outputs["quiz"],
            exercise=section_outputs["exercise"],
            interview=section_outputs["interview"],
            summary=section_outputs["summary"],
            diagram=section_outputs["diagram"],
            generation_time_ms=generation_time_ms,
            model=self.model,
        )
        reviewed = self.reviewer.review(merged)
        logger.info(
            "LESSON_PIPELINE | complete | topic=%s module=%s total_ms=%s",
            knowledge.topic_name,
            knowledge.module_title,
            int((time.monotonic() - total_started) * 1000),
        )
        return {"content_json": reviewed, "resource_links": resource_links}

    def _load_knowledge(self, **kwargs: Any) -> KnowledgeObject:
        started = time.monotonic()
        key = self.knowledge_cache.make_key(
            topic=kwargs.get("topic_name", ""),
            module=kwargs.get("module_title", ""),
            documentation_hash=_raw_documentation_hash(kwargs),
        )
        cached = self.knowledge_cache.get(key)
        if cached:
            logger.info(
                "KNOWLEDGE_CACHE | hit | key=%s lookup_ms=%s",
                key,
                int((time.monotonic() - started) * 1000),
            )
            return cached

        knowledge = self.knowledge_builder.build(**kwargs)
        key = self.knowledge_cache.make_key(
            topic=knowledge.topic_name,
            module=knowledge.module_title,
            documentation_hash=_raw_documentation_hash(kwargs),
        )
        self.knowledge_cache.set(key, knowledge)
        logger.info(
            "KNOWLEDGE_CACHE | miss | key=%s build_ms=%s",
            key,
            int((time.monotonic() - started) * 1000),
        )
        return knowledge

    def _coerce_section(
        self,
        name: str,
        result: Any,
        knowledge: KnowledgeObject,
    ) -> dict[str, Any]:
        if isinstance(result, dict):
            return result
        logger.error("LESSON_PIPELINE | section failed | section=%s result=%r", name, result)
        fallback_generator = {
            "lesson": LessonContentGenerator,
            "quiz": QuizGenerator,
            "exercise": ExerciseGenerator,
            "interview": InterviewGenerator,
            "summary": SummaryGenerator,
            "diagram": DiagramGenerator,
        }[name](None, self.model)
        return fallback_generator.fallback(knowledge)


def _raw_documentation_hash(payload: dict[str, Any]) -> str:
    raw = {
        "resources": payload.get("resources") or [],
        "mcp_context": payload.get("mcp_context") or "",
        "objectives": payload.get("learning_objectives") or [],
        "keywords": payload.get("keywords") or [],
    }
    encoded = json.dumps(raw, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
