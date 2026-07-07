"""Focused generator for core lesson teaching content."""

from __future__ import annotations

from typing import Any

from app.services.knowledge.knowledge_builder import KnowledgeObject
from app.services.lesson.base_generator import SectionGenerator, compact_context


class LessonContentGenerator(SectionGenerator):
    section_name = "lesson_generator"

    def system_prompt(self) -> str:
        return (
            "You are an expert Microsoft Certified Trainer. Teach today's lesson only. "
            "Do not create quizzes, labs, interviews, summaries, or diagrams. Output valid JSON."
        )

    def user_prompt(self, knowledge: KnowledgeObject) -> str:
        return f"""
Using only the official Microsoft Learn context below, generate core lesson content.

Return JSON with keys:
today_goal, why_this_matters, introduction, explanation, key_concepts,
real_world_example, best_practices, common_mistakes, code_walkthrough.

Rules:
- key_concepts: 5-8 objects with term and definition.
- best_practices: 4-6 strings grounded in official docs.
- common_mistakes: 3-5 objects with mistake, consequence, fix.
- code_walkthrough: title, language, code, explanation. Use code only if present.
- Do not generate quiz, exercise, interview, summary, or diagram.

Context:
{compact_context(knowledge)}
""".strip()

    def fallback(self, knowledge: KnowledgeObject) -> dict[str, Any]:
        return {
            "today_goal": f"Understand {knowledge.module_title} and how to apply it in {knowledge.topic_name}.",
            "why_this_matters": f"{knowledge.module_title} is part of practical {knowledge.topic_name} delivery and should be learned from official Microsoft guidance.",
            "introduction": f"This lesson introduces {knowledge.module_title} in the context of {knowledge.topic_name}.",
            "explanation": knowledge.documentation_summary or f"Review the official Microsoft Learn material for {knowledge.module_title}.",
            "key_concepts": [
                {"term": knowledge.module_title, "definition": f"A core concept in {knowledge.topic_name}."}
            ],
            "real_world_example": {
                "company_type": "Enterprise IT team",
                "scenario": f"A team applies {knowledge.module_title} while building a production {knowledge.topic_name} solution.",
                "lessons_learned": ["Start with official documentation.", "Validate in a sandbox.", "Document operational decisions."],
            },
            "best_practices": [
                "Use official Microsoft Learn documentation as the source of truth.",
                "Validate configuration in a non-production environment.",
                "Include security, monitoring, and cost review in the design.",
                "Keep implementation notes aligned with current Microsoft guidance.",
            ],
            "common_mistakes": [
                {"mistake": "Skipping prerequisites", "consequence": "Implementation gaps", "fix": "Review objectives and official docs first."}
            ],
            "code_walkthrough": {
                "title": "Official sample walkthrough",
                "language": "conceptual",
                "code": "",
                "explanation": "No verified sample code was available in the normalized knowledge object.",
            },
        }
