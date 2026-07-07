"""
Lesson Generation Service — Senior MCT Edition

The model acts as a Senior Microsoft Certified Trainer with 15+ years of enterprise
experience. Every lesson includes:

  - Deep technical explanation (not summaries)
  - Architecture/concept diagrams in Mermaid syntax
  - Real-world enterprise examples (named companies/scenarios)
  - Hands-on exercise calibrated to skill level
  - Interview questions (beginner + advanced)
  - Knowledge check quiz (5-8 questions)
  - Common mistakes and troubleshooting tips
  - Key takeaways

Generated ONCE per module. Cached in generated_lessons for all users.
"""

import json
import logging
import time as _time
from typing import Dict, Any, List

from groq import AsyncGroq
from app.core.config import settings
from app.services.lesson.lesson_coordinator import LessonCoordinator

logger = logging.getLogger(__name__)

_MAX_SOURCE_CHARS = 8000


def _build_context(resources: List[Dict]) -> str:
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


def _build_official_context(resources: List[Dict], mcp_context: str = "") -> str:
    """
    Build the documentation context block used by Groq.

    MCP context is first because it is the official Microsoft Learn enrichment
    source. Existing discovered resources remain as supplemental context so the
    current lesson flow keeps working if MCP is unavailable.
    """
    discovered_context = _build_context(resources)
    parts = []
    if mcp_context:
        parts.append(mcp_context)
    if discovered_context:
        parts.append("SUPPLEMENTAL DISCOVERED RESOURCES\n" + discovered_context)
    return "\n\n".join(parts)


def _skill_guidance(skill_level: str) -> str:
    return {
        "beginner":     "Assume zero prior knowledge. Use simple language. Lots of analogies. Avoid jargon unless you define it immediately.",
        "intermediate": "Assume working knowledge. Go deeper. Show real configs and code. Discuss trade-offs.",
        "advanced":     "Assume strong experience. Cover architecture decisions, performance implications, gotchas, and enterprise patterns.",
        "expert":       "Write for a principal engineer or architect. System design considerations, edge cases, cost/scale trade-offs, and enterprise governance.",
    }.get(skill_level, "Assume working knowledge.")


class LessonGeneratorService:
    def __init__(self):
        self.model = settings.GROQ_MODEL
        if not settings.GROQ_API_KEY:
            self.client = None
            logger.error(
                "LESSON_GEN | GROQ_API_KEY is not set — ALL lessons will use the "
                "fallback template. Set GROQ_API_KEY in your .env file and restart."
            )
        else:
            self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            logger.info(
                f"LESSON_GEN | Groq configured | model={self.model} | "
                f"key=...{settings.GROQ_API_KEY[-6:]}"
            )
        self.coordinator = LessonCoordinator(client=self.client, model=self.model)

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
        phase_name: str = "",
        is_milestone: bool = False,
        skill_level: str = "",
        mcp_context: str = "",
    ) -> Dict[str, Any]:
        """Generate a deep, professional lesson using Groq."""

        return await self.coordinator.generate(
            topic_name=topic_name,
            module_title=module_title,
            sequence_number=sequence_number,
            total_modules=total_modules,
            learning_objectives=learning_objectives or [],
            keywords=keywords or [],
            difficulty_level=difficulty_level,
            resources=resources or [],
            phase_name=phase_name,
            is_milestone=is_milestone,
            skill_level=skill_level or difficulty_level,
            mcp_context=mcp_context,
        )

        context = _build_official_context(resources, mcp_context)
        objectives_str = "\n".join(f"- {o}" for o in (learning_objectives or []))
        keywords_str = ", ".join(keywords or [])
        resource_links = [
            {"title": r.get("title", ""), "url": r.get("url", ""), "source": r.get("source", "")}
            for r in resources
            if r.get("url")
        ]
        effective_skill = skill_level or difficulty_level
        skill_guidance = _skill_guidance(effective_skill)
        module_type = "MILESTONE PROJECT" if is_milestone else "LESSON"
        phase_str = f" ({phase_name})" if phase_name else ""

        prompt = f"""You are a Senior Microsoft Certified Trainer with 15+ years of enterprise consulting experience.
You teach complex Microsoft technologies to professionals at Fortune 500 companies.
Your lessons are technical, deep, practical, and prepare learners for real-world work AND certification exams.

TRACK: {topic_name}
{module_type}: Module {sequence_number} of {total_modules} — {module_title}{phase_str}
SKILL LEVEL: {effective_skill.upper()}
LEARNING OBJECTIVES:
{objectives_str}
KEY TECHNOLOGIES: {keywords_str}

AUDIENCE GUIDANCE: {skill_guidance}

{"This is a MILESTONE PROJECT. Focus on a hands-on project that synthesises skills from the phase." if is_milestone else ""}

OFFICIAL DOCUMENTATION CONTEXT:
{context if context else f"Use your deep knowledge of {topic_name} — {module_title}."}

Based only on the official Microsoft documentation context above when making
Microsoft-specific claims. If official documentation is temporarily
unavailable, continue with a useful lesson from the module metadata and include
that limitation in "official_documentation_status".

Generate a COMPREHENSIVE, PROFESSIONAL lesson. Output ONLY valid JSON with EXACTLY this structure:

{{
  "module_title": "{module_title}",
  "skill_level": "{effective_skill}",
  "phase_name": "{phase_name}",
  "is_milestone": {str(is_milestone).lower()},
  "official_documentation_status": "available | temporarily_unavailable",
  "estimated_read_minutes": <integer 10-30>,
  "today_goal": "One sentence: what the learner will be able to DO after this lesson.",
  "why_this_matters": "2-3 sentences: why THIS topic matters in real enterprise work. Be specific — mention actual business scenarios, not generic phrases.",
  "introduction": "2-3 engaging sentences introducing the topic and setting context for where it fits in the broader {topic_name} ecosystem.",
  "explanation": "DEEP technical explanation. Minimum 4-6 paragraphs. Do NOT summarise — TEACH. Cover: what it is, how it works internally, when to use it vs alternatives, configuration details, and important nuances. Use precise technical language appropriate for {effective_skill} level.",
  "architecture_diagram": "A Mermaid diagram illustrating the key architecture or flow for this topic. Use graph TD, sequenceDiagram, or flowchart syntax. Must be valid Mermaid. Example: 'graph TD\\n  A[Client] --> B[Load Balancer]\\n  B --> C[VM1]\\n  B --> D[VM2]'",
  "key_concepts": [
    {{"term": "ExactTechnicalTerm", "definition": "Precise 1-2 sentence technical definition. Include context for when/why it matters."}}
  ],
  "real_world_example": {{
    "company_type": "e.g. Retail bank, SaaS startup, Healthcare provider, E-commerce platform",
    "scenario": "3-4 sentences describing a realistic enterprise scenario where this technology solves a real business problem. Be specific about the problem, the solution, and the outcome.",
    "lessons_learned": ["Insight 1 from this real-world application.", "Insight 2.", "Insight 3."]
  }},
  "common_mistakes": [
    {{"mistake": "Specific mistake professionals make", "consequence": "What goes wrong", "fix": "How to avoid/fix it"}}
  ],
  "best_practices": [
    "Specific best practice grounded in the official documentation context."
  ],
  "code_walkthrough": {{
    "title": "Code sample or command walkthrough title",
    "language": "Python, C#, Azure CLI, PowerShell, or conceptual",
    "code": "Short representative snippet or command if present in the official context; otherwise an empty string.",
    "explanation": "Explain what the sample does and why each important line or command matters."
  }},
  "practical_exercise": {{
    "title": "Hands-on exercise title",
    "objective": "What the learner will build/configure",
    "prerequisites": ["List any required setup"],
    "steps": ["Step 1: ...", "Step 2: ...", "Step 3: ...", "Step 4: ...", "Step 5: ..."],
    "expected_outcome": "Specific, measurable outcome",
    "challenge_extension": "Optional harder challenge for advanced learners"
  }},
  "questions": {{
    "beginner": [
      {{
        "question": "A foundational conceptual question testing understanding of core ideas.",
        "model_answer": "Clear, complete answer a new learner can understand."
      }},
      {{
        "question": "A second foundational question covering a different core concept.",
        "model_answer": "Clear, complete answer."
      }}
    ],
    "advanced": [
      {{
        "question": "A scenario-based question requiring architectural or trade-off reasoning.",
        "model_answer": "Detailed answer covering design decisions, edge cases, and enterprise context."
      }},
      {{
        "question": "A troubleshooting or performance question requiring deep operational knowledge.",
        "model_answer": "Detailed answer with specific steps or patterns."
      }},
      {{
        "question": "A governance, security, or cost-optimisation question at principal-engineer level.",
        "model_answer": "Detailed answer covering enterprise considerations."
      }}
    ]
  }},
  "quiz": [
    {{
      "question": "Multiple-choice question testing a specific fact, concept, or behaviour.",
      "options": ["A) First option", "B) Second option", "C) Third option", "D) Fourth option"],
      "correct_answer": "A) First option",
      "explanation": "Explain exactly why this option is correct AND why each wrong option is incorrect."
    }}
  ],
  "summary": ["Key takeaway 1", "Key takeaway 2", "Key takeaway 3", "Key takeaway 4"],
  "next_lesson_preview": "1 engaging sentence teasing the next module.",
  "further_reading": [
    {{"title": "Resource title", "url": "https://learn.microsoft.com/...", "type": "official_docs"}}
  ]
}}

STRICT RULES:
- key_concepts: exactly 5-8 terms
- common_mistakes: exactly 3-5 items
- best_practices: exactly 4-6 items, grounded in the official documentation context
- code_walkthrough: include a concise snippet only if supported by the context; otherwise explain the official sample links conceptually
- questions.beginner: EXACTLY 2 questions — both MUST be present
- questions.advanced: EXACTLY 3 questions — all 3 MUST be present
- quiz: EXACTLY 5 questions minimum, up to 8 maximum — cover different aspects of the module
- Each quiz item MUST have: question, options (exactly 4), correct_answer, explanation
- quiz options MUST start with "A) ", "B) ", "C) ", "D) " respectively
- correct_answer MUST exactly match one of the four options strings
- summary: exactly 4-6 bullet points as a JSON array of strings
- architecture_diagram: MUST be valid Mermaid syntax. Escape newlines as \\n
- further_reading: 2-4 official Microsoft/Databricks/etc. links
- Do NOT use generic phrases like "enhance your skills" or "deepen your understanding"
- Be specific, technical, and actionable
- Output ONLY valid JSON. No markdown fences. No preamble.
"""

        t0 = _time.monotonic()
        logger.info(
            f"LESSON_GEN | START | topic={topic_name} module={module_title} "
            f"skill={effective_skill} milestone={is_milestone} "
            f"groq_key_set={bool(settings.GROQ_API_KEY)}"
        )

        if not settings.GROQ_API_KEY:
            logger.error(
                f"LESSON_GEN | SKIP | GROQ_API_KEY not set — using fallback for "
                f"{topic_name}/{module_title}"
            )
            return {
                "content_json": _fallback_lesson(
                    topic_name, module_title, effective_skill, is_milestone
                ),
                "resource_links": resource_links,
            }

        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a Senior Microsoft Certified Trainer and enterprise architect. "
                            "You write deeply technical, practical, and precise educational content. "
                            "Output ONLY valid JSON. Never include markdown code fences."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                model=self.model,
                temperature=0.3,
                response_format={"type": "json_object"},
                max_tokens=8192,
            )
            latency_ms = int((_time.monotonic() - t0) * 1000)
            usage = response.usage
            result = json.loads(response.choices[0].message.content)

            logger.info(
                f"LESSON_GEN | SUCCESS | topic={topic_name} module={module_title} "
                f"latency_ms={latency_ms} tokens={getattr(usage, 'total_tokens', '?')}"
            )
            return {"content_json": result, "resource_links": resource_links}

        except Exception as exc:
            latency_ms = int((_time.monotonic() - t0) * 1000)
            logger.error(
                f"LESSON_GEN | FAILED | {topic_name}/{module_title} "
                f"latency_ms={latency_ms} | {type(exc).__name__}: {exc}",
                exc_info=True,
            )
            logger.warning(
                f"LESSON_GEN | FALLBACK | delivering generic lesson for "
                f"{topic_name}/{module_title} — check GROQ_API_KEY and network"
            )
            return {
                "content_json": _fallback_lesson(
                    topic_name, module_title, effective_skill, is_milestone
                ),
                "resource_links": resource_links,
            }


def _fallback_lesson(topic_name: str, module_title: str, skill_level: str, is_milestone: bool) -> dict:
    """Minimal fallback when Groq fails — never blocks delivery."""
    return {
        "module_title": module_title,
        "skill_level": skill_level,
        "phase_name": "",
        "is_milestone": is_milestone,
        "official_documentation_status": "temporarily_unavailable",
        "estimated_read_minutes": 10,
        "today_goal": f"Understand the fundamentals of {module_title} in {topic_name}.",
        "why_this_matters": f"{module_title} is a critical component of {topic_name} used extensively in enterprise environments.",
        "introduction": f"In this lesson we cover {module_title}, a key building block in the {topic_name} ecosystem.",
        "explanation": f"This module covers {module_title}. Refer to the official Microsoft documentation for detailed guidance.",
        "architecture_diagram": f"graph TD\n  A[{module_title}] --> B[{topic_name}]",
        "key_concepts": [
            {"term": module_title, "definition": f"Core concept in {topic_name}."}
        ],
        "real_world_example": {
            "company_type": "Enterprise",
            "scenario": f"Organizations use {module_title} to solve real-world {topic_name} challenges.",
            "lessons_learned": [f"{module_title} improves reliability and scalability."]
        },
        "common_mistakes": [
            {"mistake": "Skipping fundamentals", "consequence": "Gaps in knowledge", "fix": "Complete all prerequisite modules first."}
        ],
        "best_practices": [
            "Use the official Microsoft Learn documentation as the source of truth.",
            "Validate configuration choices in a sandbox before production rollout.",
            "Apply security, monitoring, and cost controls from the start.",
            "Keep implementation notes tied to the current Microsoft guidance.",
        ],
        "code_walkthrough": {
            "title": "Official sample walkthrough",
            "language": "conceptual",
            "code": "",
            "explanation": "Official documentation is temporarily unavailable, so review the linked Microsoft Learn resources before copying implementation code.",
        },
        "practical_exercise": {
            "title": f"Explore {module_title}",
            "objective": f"Get hands-on experience with {module_title}",
            "prerequisites": [],
            "steps": [
                f"1. Visit learn.microsoft.com and search for {module_title}",
                "2. Complete the interactive sandbox exercise",
                "3. Review the official documentation",
            ],
            "expected_outcome": f"Working understanding of {module_title}.",
            "challenge_extension": f"Try applying {module_title} in a real project scenario.",
        },
        "questions": {
            "beginner": [
                {
                    "question": f"What is {module_title} and what problem does it solve in {topic_name}?",
                    "model_answer": f"{module_title} is a core component of {topic_name} that provides essential functionality for enterprise environments."
                },
                {
                    "question": f"What are the key use cases for {module_title}?",
                    "model_answer": f"{module_title} is primarily used for building and managing {topic_name} workloads. Refer to the official Microsoft documentation for specific use cases."
                },
            ],
            "advanced": [
                {
                    "question": f"How would you design a production-grade solution using {module_title} at enterprise scale?",
                    "model_answer": "Consider high availability, disaster recovery, cost optimisation, and security hardening. Discuss trade-offs between approaches."
                },
                {
                    "question": f"What are the most common performance bottlenecks when working with {module_title} and how do you resolve them?",
                    "model_answer": "Identify bottlenecks through monitoring and diagnostics. Apply right-sizing, caching, and architectural patterns appropriate to the workload."
                },
                {
                    "question": f"How does {module_title} integrate with governance, compliance, and security policies in a regulated enterprise?",
                    "model_answer": "Apply RBAC, policy-as-code, audit logging, and integration with security information and event management tools."
                },
            ],
        },
        "quiz": [
            {
                "question": f"What is the primary purpose of {module_title}?",
                "options": [
                    f"A) Core {topic_name} functionality",
                    "B) An unrelated external service",
                    "C) A deprecated legacy feature",
                    "D) A third-party tool",
                ],
                "correct_answer": f"A) Core {topic_name} functionality",
                "explanation": f"{module_title} is a core component of {topic_name}. Options B, C, and D are incorrect because {module_title} is a native, actively maintained Microsoft feature.",
            },
            {
                "question": f"Which of the following best describes when to use {module_title}?",
                "options": [
                    f"A) When building or managing {topic_name} workloads",
                    "B) Only for development and testing environments",
                    "C) Exclusively for small-scale personal projects",
                    "D) As a replacement for on-premises infrastructure only",
                ],
                "correct_answer": f"A) When building or managing {topic_name} workloads",
                "explanation": f"{module_title} is designed for production {topic_name} workloads at any scale, not limited to dev/test or personal use.",
            },
        ],
        "summary": [
            f"{module_title} is an important building block within {topic_name}.",
            "Refer to the official Microsoft Learn documentation for detailed guidance.",
            "Hands-on practice in a sandbox environment accelerates understanding.",
            "Apply what you learn to a real-world scenario to solidify the concepts.",
        ],
        "next_lesson_preview": "Continue your learning journey in the next module.",
        "further_reading": [
            {"title": "Microsoft Learn", "url": "https://learn.microsoft.com", "type": "official_docs"}
        ]
    }
