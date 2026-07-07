"""Focused Mermaid diagram generator."""

from __future__ import annotations

from typing import Any

from app.services.knowledge.knowledge_builder import KnowledgeObject
from app.services.lesson.base_generator import SectionGenerator, compact_context


class DiagramGenerator(SectionGenerator):
    section_name = "diagram_generator"

    def system_prompt(self) -> str:
        return "You generate valid Mermaid diagrams for Microsoft architecture lessons. Output valid JSON."

    def user_prompt(self, knowledge: KnowledgeObject) -> str:
        return f"""
Generate Mermaid only.
Return JSON with keys: architecture_diagram, diagram_type.
Rules:
- architecture_diagram must be valid Mermaid using graph TD, flowchart TD, or sequenceDiagram.
- Do not generate explanation, quiz, lab, interview, or summary.
- If context is insufficient, return "No diagram available."

Context:
{compact_context(knowledge)}
""".strip()

    def fallback(self, knowledge: KnowledgeObject) -> dict[str, Any]:
        return {
            "architecture_diagram": f"graph TD\n  A[{knowledge.module_title}] --> B[{knowledge.topic_name}]",
            "diagram_type": "architecture",
        }
