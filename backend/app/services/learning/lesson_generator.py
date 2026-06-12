"""
Lesson Generation Service — Groq-powered educational content generation.

Called ONCE per module. The result is stored in generated_lessons and
reused for all users enrolled in the same topic.

Input:  topic name, module title, learning objectives, extracted source content
Output: structured JSON with explanation, key concepts, quiz, exercise, etc.
"""

import json
import logging
import time as _time
from typing import Dict, Any, List

from groq import AsyncGroq
from app.core.config import settings

logger = logging.getLogger(__name__)

_MAX_SOURCE_CHARS = 6000   # total context chars fed to the LLM


def _build_context(resources: List[Dict]) -> str:
    """Build a compact source context string from scraped resources."""
    parts = []
    remaining = _MAX_SOURCE_CHARS
    for res in resources:
        content = (res.get("content") or "")[:remaining]
        if content:
            parts.append(f"--- Source: {res['url']} ---\n{content}")
            remaining -= len(content)
        if remaining <= 0:
            break
    return "\n\n".join(parts)


class LessonGeneratorService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    async def generate_lesson(
        self,
        topic_name: str,
        module_title: str,
        sequence_number: int,
        total_modules: int,
        learning_objectives: List[str],
        keywords: List[str],
        difficulty_level: str,
        resources: List[Dict],
    ) -> Dict[str, Any]:
        """
        Generate a structured educational lesson using Groq.

        Returns a dict matching the LessonContent schema.
        """
        context = _build_context(resources)
        objectives_str = "\n".join(f"- {o}" for o in (learning_objectives or []))
        keywords_str = ", ".join(keywords or [])
        resource_links = [
            {"title": r.get("title", ""), "url": r["url"], "source": r.get("source", "")}
            for r in resources
        ]

        prompt = f"""You are an expert Microsoft technology instructor creating a structured learning lesson.

TOPIC: {topic_name}
MODULE: {sequence_number} of {total_modules} — {module_title}
DIFFICULTY: {difficulty_level}
LEARNING OBJECTIVES:
{objectives_str}
KEY TERMS: {keywords_str}

SOURCE MATERIAL (from official Microsoft documentation):
{context if context else "Use your knowledge of this Microsoft technology."}

Create a comprehensive, engaging lesson for a professional learner.

Output ONLY valid JSON matching this EXACT structure:
{{
  "module_title": "{module_title}",
  "difficulty_level": "{difficulty_level}",
  "estimated_read_minutes": <integer 5-25>,
  "introduction": "2-3 sentence friendly introduction that explains what this lesson covers and why it matters.",
  "explanation": "Clear, detailed explanation of the topic. 3-5 paragraphs. Beginner-friendly but technically accurate. Use analogies where helpful.",
  "key_concepts": [
    {{"term": "Term Name", "definition": "Clear 1-2 sentence definition"}}
  ],
  "real_world_example": "A concrete, realistic scenario showing how this is used in practice at a company or project. 2-3 sentences.",
  "practical_exercise": {{
    "title": "Exercise title",
    "description": "Step-by-step exercise a learner can do to practice this concept. Include 3-5 numbered steps.",
    "expected_outcome": "What the learner achieves by completing this exercise."
  }},
  "quiz": [
    {{
      "question": "Quiz question?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "explanation": "Why this answer is correct."
    }}
  ],
  "summary": "3-4 bullet points summarising the key takeaways from this lesson.",
  "next_lesson_preview": "1 sentence teaser for the next module in the learning path."
}}

Rules:
- Include exactly 4-6 key_concepts
- Include exactly 3-5 quiz questions
- summary must be a list of strings
- Output ONLY valid JSON. No markdown. No preamble. No trailing text.
"""

        t0 = _time.monotonic()
        logger.info(
            f"LESSON_GEN | START | topic={topic_name} module={module_title} "
            f"seq={sequence_number} difficulty={difficulty_level} "
            f"resources={len(resources)}"
        )

        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional Microsoft technology educator. "
                            "You write clear, engaging, technically accurate lessons. "
                            "Output only valid JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                model=self.model,
                temperature=0.4,
                response_format={"type": "json_object"},
            )
            latency_ms = int((_time.monotonic() - t0) * 1000)
            usage = response.usage
            result = json.loads(response.choices[0].message.content)

            logger.info(
                f"LESSON_GEN | SUCCESS | topic={topic_name} module={module_title} "
                f"latency_ms={latency_ms} "
                f"total_tokens={getattr(usage, 'total_tokens', '?')}"
            )
            return {"content_json": result, "resource_links": resource_links}

        except Exception as exc:
            latency_ms = int((_time.monotonic() - t0) * 1000)
            logger.error(
                f"LESSON_GEN | FAILED | topic={topic_name} module={module_title} "
                f"latency_ms={latency_ms} | {exc}",
                exc_info=True,
            )
            # Fallback: return a minimal lesson so delivery is never blocked
            return {
                "content_json": {
                    "module_title": module_title,
                    "difficulty_level": difficulty_level,
                    "estimated_read_minutes": 10,
                    "introduction": f"Welcome to this lesson on {module_title} in {topic_name}.",
                    "explanation": f"This module covers {module_title}. Please refer to Microsoft Learn for detailed documentation.",
                    "key_concepts": [{"term": module_title, "definition": f"Core concept in {topic_name}."}],
                    "real_world_example": f"Professionals use {module_title} to solve real-world {topic_name} challenges.",
                    "practical_exercise": {
                        "title": f"Explore {module_title}",
                        "description": f"1. Visit learn.microsoft.com\n2. Search for {module_title}\n3. Complete the interactive module",
                        "expected_outcome": f"Understanding of {module_title} fundamentals.",
                    },
                    "quiz": [
                        {
                            "question": f"What is the primary purpose of {module_title}?",
                            "options": [
                                f"Core functionality of {topic_name}",
                                "Unrelated concept",
                                "Legacy feature",
                                "Third-party tool",
                            ],
                            "correct_answer": f"Core functionality of {topic_name}",
                            "explanation": f"{module_title} is a core component of {topic_name}.",
                        }
                    ],
                    "summary": [
                        f"{module_title} is an important part of {topic_name}.",
                        "Refer to official Microsoft documentation for details.",
                    ],
                    "next_lesson_preview": "Continue your learning journey in the next module.",
                },
                "resource_links": resource_links,
            }
