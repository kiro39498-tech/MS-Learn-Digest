"""
Learning Newsletter Generator

Orchestrates the full lesson pipeline for one user subscription:
  1. Get current module from subscription
  2. Check generated_lessons cache — reuse if exists
  3. If no cached lesson: discover resources → generate with Groq → cache
  4. Render HTML email with Jinja2 learning template
  5. Send via SMTP
  6. Advance module progress

This is completely separate from DigestGenerator.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.learning import UserLearningSubscription
from app.repositories.learning_repository import LearningRepository
from app.services.email.smtp_client import EmailClient
from app.services.learning.resource_discovery import discover_resources
from app.services.learning.lesson_generator import LessonGeneratorService

logger = logging.getLogger(__name__)


def _get_template_env() -> Environment:
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "templates",
    )
    return Environment(loader=FileSystemLoader(template_dir), autoescape=True)


class LearningNewsletterGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.repo = LearningRepository(db)
        self.lesson_svc = LessonGeneratorService()
        self.email_client = EmailClient()
        self.env = _get_template_env()

    async def deliver(self, sub: UserLearningSubscription) -> bool:
        """
        Full pipeline: discover → generate (or load from cache) → render → send → advance.
        Returns True if email was delivered successfully.
        """
        topic = self.repo.get_topic_by_id(sub.topic_id)
        if not topic:
            logger.error(f"LEARNING | sub={sub.id} | topic not found")
            return False

        module = self.repo.get_module(sub.topic_id, sub.current_module_sequence)
        if not module:
            logger.warning(
                f"LEARNING | sub={sub.id} topic={topic.name} | "
                f"no module at seq={sub.current_module_sequence} — marking complete"
            )
            sub.status = "completed"
            sub.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            return False

        tag = f"user={sub.user_id} topic={topic.name} seq={module.sequence_number}"
        logger.info(f"LEARNING | {tag} | START")

        # ── 1. Get or generate lesson ──────────────────────────────────────
        lesson = self.repo.get_generated_lesson(module.id)

        if lesson:
            logger.info(f"LEARNING | {tag} | CACHE HIT lesson_id={lesson.id}")
            content_json = lesson.content_json or {}
            resource_links = lesson.resource_links or []
        else:
            logger.info(f"LEARNING | {tag} | CACHE MISS — generating lesson")

            # Resource discovery
            resources = discover_resources(
                topic_name=topic.name,
                module_title=module.title,
                keywords=module.keywords or [],
            )
            logger.info(f"LEARNING | {tag} | discovered {len(resources)} resources")

            # Groq generation
            # Get next module title for "next lesson preview"
            next_module = self.repo.get_module(sub.topic_id, module.sequence_number + 1)

            generated = await self.lesson_svc.generate_lesson(
                topic_name=topic.name,
                module_title=module.title,
                sequence_number=module.sequence_number,
                total_modules=topic.total_modules,
                learning_objectives=module.learning_objectives or [],
                keywords=module.keywords or [],
                difficulty_level=module.difficulty_level,
                resources=resources,
            )
            content_json = generated["content_json"]
            resource_links = generated["resource_links"]

            # Inject next lesson title if AI didn't produce one
            if next_module and not content_json.get("next_lesson_preview"):
                content_json["next_lesson_preview"] = (
                    f"Next: Module {next_module.sequence_number} — {next_module.title}"
                )

            # Cache the lesson
            lesson = self.repo.save_generated_lesson(
                topic_id=sub.topic_id,
                module_id=module.id,
                generated_content="",   # filled after render
                content_json=content_json,
                resource_links=resource_links,
                model=settings.GROQ_MODEL,
            )

        # ── 2. Render HTML ─────────────────────────────────────────────────
        user = sub.user
        user_name = (user.name.split(" ")[0] if user and user.name else "Learner")

        next_module = self.repo.get_module(sub.topic_id, module.sequence_number + 1)
        progress_pct = int((module.sequence_number / topic.total_modules) * 100)

        try:
            template = self.env.get_template("learning_email.html")
            html = template.render(
                topic_name=topic.name,
                topic_icon=topic.icon or "📚",
                module_number=module.sequence_number,
                total_modules=topic.total_modules,
                module_title=module.title,
                difficulty_level=module.difficulty_level,
                estimated_read_minutes=content_json.get("estimated_read_minutes", 10),
                user_name=user_name,
                introduction=content_json.get("introduction", ""),
                explanation=content_json.get("explanation", ""),
                key_concepts=content_json.get("key_concepts", []),
                real_world_example=content_json.get("real_world_example", ""),
                practical_exercise=content_json.get("practical_exercise", {}),
                quiz=content_json.get("quiz", []),
                summary=content_json.get("summary", []),
                next_lesson_preview=content_json.get("next_lesson_preview", ""),
                resource_links=resource_links,
                progress_pct=progress_pct,
                frontend_url=settings.FRONTEND_URL,
                generated_at=datetime.now(timezone.utc).strftime("%B %d, %Y"),
            )
        except Exception as exc:
            logger.error(f"LEARNING | {tag} | RENDER FAILED | {exc}", exc_info=True)
            return False

        # Update cached HTML if it was just generated
        if lesson and not lesson.generated_content:
            lesson.generated_content = html
            self.db.commit()

        # ── 3. Send email ──────────────────────────────────────────────────
        user_email = user.email if user else None
        if not user_email:
            logger.error(f"LEARNING | {tag} | no user email")
            return False

        subject = (
            f"📚 {topic.name} Learning Track — Day {module.sequence_number}: {module.title}"
        )
        sent = self.email_client.send_email(
            recipient=user_email,
            subject=subject,
            html_body=html,
        )

        if sent:
            logger.info(f"LEARNING | {tag} | EMAIL SENT to {user_email}")
            self.repo.advance_module(sub)
        else:
            logger.error(f"LEARNING | {tag} | EMAIL FAILED to {user_email}")
            self.repo.mark_sent(sub)   # still advance last_sent to avoid retry loops

        return sent
