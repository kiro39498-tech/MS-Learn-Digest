"""Merge modular generator outputs into the existing lesson JSON contract."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import time

from app.services.knowledge.knowledge_builder import KnowledgeObject
from app.services.lesson.base_generator import official_reading


class LessonMerger:
    def merge(
        self,
        *,
        knowledge: KnowledgeObject,
        lesson: dict[str, Any],
        quiz: dict[str, Any],
        exercise: dict[str, Any],
        interview: dict[str, Any],
        summary: dict[str, Any],
        diagram: dict[str, Any],
        generation_time_ms: int,
        model: str,
    ) -> dict[str, Any]:
        started = time.monotonic()
        content = {
            "module_title": knowledge.module_title,
            "skill_level": knowledge.skill_level,
            "phase_name": knowledge.phase_name,
            "is_milestone": knowledge.is_milestone,
            "official_documentation_status": knowledge.source_status,
            "estimated_read_minutes": 15,
            **lesson,
            **diagram,
            **exercise,
            **interview,
            **summary,
            **quiz,
            "further_reading": official_reading(knowledge),
            "metadata": {
                "pipeline": "modular_lesson_generation",
                "generator_version": "2.0.0",
                "knowledge_hash": knowledge.documentation_hash,
                "documentation_hash": knowledge.documentation_hash,
                "generation_time_ms": generation_time_ms,
                "merge_time_ms": int((time.monotonic() - started) * 1000),
                "model": model,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "lesson": lesson,
            "exercise": exercise.get("practical_exercise", exercise),
            "interview": interview.get("questions", interview),
            "diagram": diagram,
        }
        if "hands_on_activity" not in content:
            content["hands_on_activity"] = content.get("practical_exercise", {})
        return content
