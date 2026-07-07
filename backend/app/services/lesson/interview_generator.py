"""Focused interview question generator."""

from __future__ import annotations

from typing import Any

from app.services.knowledge.knowledge_builder import KnowledgeObject
from app.services.lesson.base_generator import SectionGenerator, compact_context


class InterviewGenerator(SectionGenerator):
    section_name = "interview_generator"

    def system_prompt(self) -> str:
        return "You are a senior Microsoft cloud interviewer. Generate interview questions only. Output valid JSON."

    def user_prompt(self, knowledge: KnowledgeObject) -> str:
        return f"""
Generate interview questions for this module.
Return JSON with key questions:
beginner: 2 questions, intermediate: 2 questions, advanced: 3 questions,
scenario: 2 questions, enterprise: 2 questions.
Each item must have question and model_answer.
Do not generate lesson, quiz, lab, summary, or diagram.

Context:
{compact_context(knowledge)}
""".strip()

    def fallback(self, knowledge: KnowledgeObject) -> dict[str, Any]:
        beginner = [
            {
                "question": f"What problem does {knowledge.module_title} solve?",
                "model_answer": f"It addresses a core implementation need in {knowledge.topic_name}; the exact behavior should be explained from official Microsoft documentation.",
            },
            {
                "question": f"Where should you verify details about {knowledge.module_title}?",
                "model_answer": "Use official Microsoft Learn documentation and product references.",
            },
        ]
        advanced = [
            {
                "question": f"How would you design a production use of {knowledge.module_title}?",
                "model_answer": "Discuss reliability, security, operations, cost, and documented platform constraints.",
            },
            {
                "question": f"What trade-offs matter when adopting {knowledge.module_title}?",
                "model_answer": "Evaluate complexity, operational fit, governance requirements, and supported product capabilities.",
            },
            {
                "question": f"How would you troubleshoot an issue with {knowledge.module_title}?",
                "model_answer": "Start from documented diagnostics, validate configuration, inspect logs/metrics, and isolate recent changes.",
            },
        ]
        return {
            "questions": {
                "beginner": beginner,
                "intermediate": beginner,
                "advanced": advanced,
                "scenario": advanced[:2],
                "enterprise": advanced[:2],
            }
        }
