"""Shared helpers for focused lesson generators."""

from __future__ import annotations

from typing import Any
import json
import logging
import time

from app.services.knowledge.knowledge_builder import KnowledgeObject

logger = logging.getLogger(__name__)

_MAX_CONTEXT_CHARS = 4500


class SectionGenerator:
    section_name = "section"

    def __init__(self, client: Any = None, model: str = "") -> None:
        self.client = client
        self.model = model

    async def generate(self, knowledge: KnowledgeObject) -> dict[str, Any]:
        started = time.monotonic()
        if not self.client:
            result = self.fallback(knowledge)
            self._log_complete(started, fallback=True)
            return result
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt()},
                    {"role": "user", "content": self.user_prompt(knowledge)},
                ],
                model=self.model,
                temperature=0.25,
                response_format={"type": "json_object"},
                max_tokens=self.max_tokens(),
            )
            result = json.loads(response.choices[0].message.content)
            self._log_complete(started, fallback=False)
            return result
        except Exception as exc:
            logger.error(
                "%s | failed | %s: %s",
                self.section_name.upper(),
                type(exc).__name__,
                exc,
                exc_info=True,
            )
            result = self.fallback(knowledge)
            self._log_complete(started, fallback=True)
            return result

    def system_prompt(self) -> str:
        return "You generate one focused section of a Microsoft Learn lesson. Output only valid JSON."

    def user_prompt(self, knowledge: KnowledgeObject) -> str:
        raise NotImplementedError

    def fallback(self, knowledge: KnowledgeObject) -> dict[str, Any]:
        raise NotImplementedError

    def max_tokens(self) -> int:
        return 2048

    def _log_complete(self, started: float, fallback: bool) -> None:
        logger.info(
            "%s | complete | latency_ms=%s fallback=%s",
            self.section_name.upper(),
            int((time.monotonic() - started) * 1000),
            fallback,
        )


def compact_context(knowledge: KnowledgeObject) -> str:
    docs = []
    for item in knowledge.official_documentation[:5]:
        docs.append(
            f"Title: {item.get('title')}\n"
            f"URL: {item.get('url')}\n"
            f"Summary: {item.get('summary')}\n"
            f"Text: {item.get('content', '')[:900]}"
        )
    context = "\n\n".join([
        f"Topic: {knowledge.topic_name}",
        f"Module: {knowledge.module_title}",
        f"Skill level: {knowledge.skill_level}",
        f"Objectives: {', '.join(knowledge.learning_objectives)}",
        f"Keywords: {', '.join(knowledge.keywords)}",
        f"Documentation summary: {knowledge.documentation_summary}",
        "Official docs:\n" + "\n\n".join(docs),
    ])
    return context[:_MAX_CONTEXT_CHARS]


def official_reading(knowledge: KnowledgeObject, limit: int = 4) -> list[dict[str, str]]:
    return [
        {"title": item.get("title", "Microsoft Learn"), "url": item.get("url", ""), "type": "official_docs"}
        for item in knowledge.official_documentation[:limit]
        if item.get("url")
    ] or [{"title": "Microsoft Learn", "url": "https://learn.microsoft.com", "type": "official_docs"}]
