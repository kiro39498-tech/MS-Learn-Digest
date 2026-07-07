"""Focused summary and revision-note generator."""

from __future__ import annotations

from typing import Any

from app.services.knowledge.knowledge_builder import KnowledgeObject
from app.services.lesson.base_generator import SectionGenerator, compact_context


class SummaryGenerator(SectionGenerator):
    section_name = "summary_generator"

    def system_prompt(self) -> str:
        return "You create concise revision material for Microsoft technical learners. Output valid JSON."

    def user_prompt(self, knowledge: KnowledgeObject) -> str:
        return f"""
Generate revision material only.
Return JSON with keys: summary, revision_notes, cheat_sheet, memory_tips, next_lesson_preview.
Rules:
- summary: 4-6 key takeaways.
- cheat_sheet: compact facts or commands if supported by context.
- Do not generate lesson, quiz, lab, interview, or diagram.

Context:
{compact_context(knowledge)}
""".strip()

    def fallback(self, knowledge: KnowledgeObject) -> dict[str, Any]:
        return {
            "summary": [
                f"{knowledge.module_title} is an important topic within {knowledge.topic_name}.",
                "Official Microsoft Learn documentation should drive implementation details.",
                "Hands-on validation helps turn concepts into operational skill.",
                "Security, reliability, and governance should be considered early.",
            ],
            "revision_notes": [knowledge.documentation_summary or f"Review {knowledge.module_title} in Microsoft Learn."],
            "cheat_sheet": knowledge.official_urls[:4],
            "memory_tips": ["Tie each feature to the production problem it solves."],
            "next_lesson_preview": "Continue with the next module in the learning path.",
        }
