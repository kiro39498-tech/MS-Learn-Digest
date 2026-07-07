"""Focused hands-on exercise generator."""

from __future__ import annotations

from typing import Any

from app.services.knowledge.knowledge_builder import KnowledgeObject
from app.services.lesson.base_generator import SectionGenerator, compact_context


class ExerciseGenerator(SectionGenerator):
    section_name = "exercise_generator"

    def system_prompt(self) -> str:
        return "You are a Microsoft Learn lab author. Generate a practical exercise only. Output valid JSON."

    def user_prompt(self, knowledge: KnowledgeObject) -> str:
        return f"""
Generate a hands-on lab for this module.
Return JSON with key practical_exercise containing:
title, objective, prerequisites, steps, expected_outcome, challenge_extension.
Do not generate quizzes, interviews, diagrams, or lesson explanation.

Context:
{compact_context(knowledge)}
""".strip()

    def fallback(self, knowledge: KnowledgeObject) -> dict[str, Any]:
        return {
            "practical_exercise": {
                "title": f"Explore {knowledge.module_title}",
                "objective": f"Apply the core ideas from {knowledge.module_title}.",
                "prerequisites": ["Access to Microsoft Learn", "A sandbox or test subscription if configuration is required"],
                "steps": [
                    f"Open the official Microsoft Learn page for {knowledge.module_title}.",
                    "Identify the prerequisites and supported configuration options.",
                    "Follow one documented quickstart or example in a non-production environment.",
                    "Record the settings used and the result observed.",
                    "Compare the result against the documented expected behavior.",
                ],
                "expected_outcome": f"A verified understanding of how {knowledge.module_title} works in practice.",
                "challenge_extension": "Adapt the exercise for a realistic enterprise requirement.",
            }
        }
