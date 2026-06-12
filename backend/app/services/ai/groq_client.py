"""
Groq API Client — Batch digest generation.

Called ONLY during digest generation, never during sync or ingestion.
Accepts a list of catalog items and produces:
  - executive_summary : 2-3 sentence overview of the entire digest
  - items[]           : per-item newsletter_summary, why_it_matters, key_takeaways

One API call per digest (not per module).
"""

import json
import logging
from typing import Dict, Any, List
from groq import AsyncGroq
from app.core.config import settings

logger = logging.getLogger(__name__)

# Approximate token budget per item in the input payload.
# title ≈ 15 words, summary ≈ 100 words → ~115 words / ~150 tokens per item.
# At 30 items that's ~4,500 tokens input — safely under limits.
_MAX_SUMMARY_WORDS = 100


def _truncate(text: str, max_words: int) -> str:
    """Truncate text to at most max_words words."""
    words = (text or "").split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


class GroqClient:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not set. AI features will fail.")
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = settings.GROQ_MODEL

    async def generate_digest(
        self,
        items: List[Dict[str, Any]],
        topic_names: List[str],
        frequency: str,
    ) -> Dict[str, Any]:
        """
        Generate a full digest from a list of catalog items in one Groq call.

        Args:
            items: list of dicts with keys uid, title, summary
            topic_names: human-readable topic labels for context
            frequency: 'daily' | 'weekly' | 'biweekly' | 'monthly'

        Returns: {
            "executive_summary": "...",
            "items": [
                {
                    "uid": "...",
                    "newsletter_summary": "...",
                    "why_it_matters": "...",
                    "key_takeaways": ["...", "...", "..."]
                }
            ]
        }
        """
        window_label = {
            "daily": "the last 24 hours",
            "weekly": "the last 7 days",
            "biweekly": "the last 14 days",
            "monthly": "the last 30 days",
        }.get(frequency, "the recent period")

        # Build compact input — truncate summaries to control token usage
        payload_items = [
            {
                "uid": item["uid"],
                "title": item["title"],
                "summary": _truncate(item.get("summary") or "", _MAX_SUMMARY_WORDS),
            }
            for item in items
        ]

        topics_str = ", ".join(topic_names) if topic_names else "Microsoft Learn"

        prompt = f"""You are writing a Microsoft Learn newsletter for professionals interested in: {topics_str}.

The newsletter covers Microsoft Learn updates from {window_label}.

Here are the {len(payload_items)} modules/learning paths to include:

{json.dumps(payload_items, indent=2)}

Output a single JSON object with EXACTLY this structure:
{{
  "executive_summary": "A 2-3 sentence overview of the most important updates this period. Be specific about technologies.",
  "items": [
    {{
      "uid": "<copy uid from input>",
      "newsletter_summary": "1-2 sentence engaging description for a professional newsletter reader.",
      "why_it_matters": "1 sentence explaining the concrete business or technical value.",
      "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"]
    }}
  ]
}}

Rules:
- Include every uid from the input in items[].
- Be specific and practical. Avoid generic phrases like "enhance your skills".
- Output ONLY valid JSON. No markdown. No preamble.
"""

        import time as _time
        prompt_chars = len(prompt)
        # Rough token estimate: ~4 chars per token
        estimated_tokens = prompt_chars // 4
        logger.info(
            f"GROQ | generate_digest | START | "
            f"items={len(items)} topics={topic_names} frequency={frequency} "
            f"prompt_chars={prompt_chars} estimated_input_tokens~={estimated_tokens}"
        )
        t0 = _time.monotonic()

        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional technical newsletter writer. Output only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model=self.model,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            latency_ms = int((_time.monotonic() - t0) * 1000)
            usage = response.usage
            result = json.loads(response.choices[0].message.content)
            logger.info(
                f"GROQ | generate_digest | SUCCESS | "
                f"latency_ms={latency_ms} "
                f"prompt_tokens={getattr(usage, 'prompt_tokens', '?')} "
                f"completion_tokens={getattr(usage, 'completion_tokens', '?')} "
                f"total_tokens={getattr(usage, 'total_tokens', '?')} "
                f"items_in_response={len(result.get('items', []))} "
                f"executive_summary_chars={len(result.get('executive_summary', ''))}"
            )
            return result
        except Exception as exc:
            latency_ms = int((_time.monotonic() - t0) * 1000)
            logger.error(
                f"GROQ | generate_digest | FAILED | latency_ms={latency_ms} | {exc}",
                exc_info=True,
            )
            raise
