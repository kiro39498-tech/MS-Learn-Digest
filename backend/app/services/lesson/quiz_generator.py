"""Focused quiz generator."""

from __future__ import annotations

from typing import Any

from app.services.knowledge.knowledge_builder import KnowledgeObject
from app.services.lesson.base_generator import SectionGenerator, compact_context


class QuizGenerator(SectionGenerator):
    section_name = "quiz_generator"

    def system_prompt(self) -> str:
        return (
            "You are an Azure certification question writer. Generate assessment questions only. "
            "Output valid JSON."
        )

    def user_prompt(self, knowledge: KnowledgeObject) -> str:
        return f"""
Generate 5-10 certification-quality multiple-choice questions for this module.
Return JSON: {{"quiz": [{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}]}}
Rules:
- Exactly 4 options per question.
- correct_answer must exactly match an option.
- Include scenario questions and clear answer explanations.
- Do not generate lesson content.

Context:
{compact_context(knowledge)}
""".strip()

    def fallback(self, knowledge: KnowledgeObject) -> dict[str, Any]:
        return {
            "quiz": [
                {
                    "question": f"What is the best first source for implementing {knowledge.module_title}?",
                    "options": [
                        "A) Official Microsoft Learn documentation",
                        "B) Unverified blog comments",
                        "C) Random generated examples",
                        "D) Deprecated product notes",
                    ],
                    "correct_answer": "A) Official Microsoft Learn documentation",
                    "explanation": "Official Microsoft Learn documentation is the authoritative source. The other options are not reliable implementation references.",
                }
            ]
        }
