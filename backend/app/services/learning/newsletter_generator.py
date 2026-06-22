"""
Learning Newsletter Generator — Enhanced Edition

Pipeline per user subscription:
  1. Resolve current module + phase info
  2. Check generated_lessons cache
  3. Cache miss: resource discovery → Groq generation → cache
  4. Render professional HTML email
  5. Send via SMTP
  6. Record analytics + update streak
  7. Advance module progress
"""

import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.learning import UserLearningSubscription, LearningAnalytics
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


def _update_streak(sub: UserLearningSubscription, db: Session) -> int:
    """Update consecutive day streak. Returns current streak."""
    now = datetime.now(timezone.utc)
    if sub.last_sent_at is None:
        sub.current_streak_days = 1
    else:
        diff = (now - sub.last_sent_at).days
        if diff <= 1:
            sub.current_streak_days = (sub.current_streak_days or 0) + 1
        else:
            sub.current_streak_days = 1  # streak broken
    sub.longest_streak_days = max(
        sub.longest_streak_days or 0,
        sub.current_streak_days,
    )
    sub.total_lessons_sent = (sub.total_lessons_sent or 0) + 1
    return sub.current_streak_days


def _record_analytics(
    db: Session,
    sub: UserLearningSubscription,
    module,
) -> None:
    """Write one row to learning_analytics."""
    try:
        record = LearningAnalytics(
            id=uuid.uuid4(),
            subscription_id=sub.id,
            user_id=sub.user_id,
            topic_id=sub.topic_id,
            module_id=module.id,
            module_sequence=module.sequence_number,
            sent_at=datetime.now(timezone.utc),
            difficulty_level=module.difficulty_level,
            phase_name=getattr(module, "phase_name", None),
            is_milestone=getattr(module, "is_milestone", False),
        )
        db.add(record)
    except Exception as exc:
        logger.warning(f"ANALYTICS | failed to record: {exc}")


class LearningNewsletterGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.repo = LearningRepository(db)
        self.lesson_svc = LessonGeneratorService()
        self.email_client = EmailClient()
        self.env = _get_template_env()

    async def deliver(self, sub: UserLearningSubscription) -> bool:
        topic = self.repo.get_topic_by_id(sub.topic_id)
        if not topic:
            logger.error(f"LEARNING | sub={sub.id} | topic not found")
            return False

        module = self.repo.get_module(sub.topic_id, sub.current_module_sequence)
        if not module:
            logger.warning(
                f"LEARNING | sub={sub.id} topic={topic.name} "
                f"seq={sub.current_module_sequence} | no module — marking complete"
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
            logger.info(f"LEARNING | {tag} | CACHE HIT")
            content_json = lesson.content_json or {}
            resource_links = lesson.resource_links or []
        else:
            logger.info(f"LEARNING | {tag} | CACHE MISS — generating")
            resources = discover_resources(
                topic_name=topic.name,
                module_title=module.title,
                keywords=module.keywords or [],
            )
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
                phase_name=getattr(module, "phase_name", ""),
                is_milestone=getattr(module, "is_milestone", False),
                skill_level=getattr(module, "skill_level", module.difficulty_level),
            )
            content_json = generated["content_json"]
            resource_links = generated["resource_links"]

            if next_module and not content_json.get("next_lesson_preview"):
                content_json["next_lesson_preview"] = (
                    f"Next: Module {next_module.sequence_number} — {next_module.title}"
                )

            lesson = self.repo.save_generated_lesson(
                topic_id=sub.topic_id,
                module_id=module.id,
                generated_content="",
                content_json=content_json,
                resource_links=resource_links,
                model=settings.GROQ_MODEL,
            )

        # ── 2. Render HTML ─────────────────────────────────────────────────
        user = sub.user
        user_name = (user.name.split(" ")[0] if user and user.name else "Learner")
        next_module = self.repo.get_module(sub.topic_id, module.sequence_number + 1)
        progress_pct = int((module.sequence_number / max(topic.total_modules, 1)) * 100)
        modules_remaining = topic.total_modules - module.sequence_number
        streak = sub.current_streak_days or 0

        # Estimated completion date
        freq_days = {"daily": 1, "weekly": 7, "biweekly": 14}.get(sub.frequency, 7)
        estimated_done = (
            datetime.now(timezone.utc) + timedelta(days=modules_remaining * freq_days)
        ).strftime("%B %Y") if modules_remaining > 0 else "Almost there!"

        try:
            template = self.env.get_template("learning_email.html")
            html = template.render(
                # Track info
                topic_name=topic.name,
                topic_icon=topic.icon or "📚",
                total_modules=topic.total_modules,
                # Module info
                module_number=module.sequence_number,
                module_title=module.title,
                difficulty_level=module.difficulty_level,
                skill_level=getattr(module, "skill_level", module.difficulty_level),
                phase_name=getattr(module, "phase_name", ""),
                is_milestone=getattr(module, "is_milestone", False),
                estimated_read_minutes=content_json.get("estimated_read_minutes", 15),
                # Progress
                progress_pct=progress_pct,
                modules_remaining=modules_remaining,
                estimated_completion=estimated_done,
                # Learner coaching
                user_name=user_name,
                streak_days=streak,
                frequency=sub.frequency,
                # Lesson content — new learning-focused fields
                today_goal=content_json.get("today_goal", ""),
                why_this_matters=content_json.get("why_this_matters", ""),
                business_relevance=content_json.get("business_relevance", ""),
                introduction=content_json.get("introduction", ""),
                explanation=content_json.get("explanation", ""),
                architecture_diagram=content_json.get("architecture_diagram", ""),
                key_concepts=content_json.get("key_concepts", []),
                real_world_example=content_json.get("real_world_example", {}),
                # Hands-on activity (new field name; fallback to old practical_exercise)
                hands_on_activity=content_json.get("hands_on_activity", {}),
                practical_exercise=content_json.get("practical_exercise", {}),
                common_mistakes=content_json.get("common_mistakes", []),
                troubleshooting_tips=content_json.get("troubleshooting_tips", []),
                best_practices=content_json.get("best_practices", []),
                summary=content_json.get("summary", []),
                next_lesson_preview=content_json.get("next_lesson_preview", ""),
                further_reading=content_json.get("further_reading", []),
                resource_links=resource_links,
                # Metadata
                frontend_url=settings.FRONTEND_URL,
                generated_at=datetime.now(timezone.utc).strftime("%B %d, %Y"),
            )
        except Exception as exc:
            logger.error(f"LEARNING | {tag} | RENDER FAILED | {exc}", exc_info=True)
            return False

        if lesson and not lesson.generated_content:
            lesson.generated_content = html
            self.db.commit()

        # ── 3. Send ────────────────────────────────────────────────────────
        user_email = user.email if user else None
        if not user_email:
            logger.error(f"LEARNING | {tag} | no email")
            return False

        milestone_prefix = "🏆 MILESTONE — " if getattr(module, "is_milestone", False) else ""
        subject = (
            f"📚 {topic.name} — {milestone_prefix}"
            f"Module {module.sequence_number}: {module.title}"
        )
        sent = self.email_client.send_email(
            recipient=user_email,
            subject=subject,
            html_body=html,
        )

        # ── 4. Analytics + advance ─────────────────────────────────────────
        if sent:
            logger.info(f"LEARNING | {tag} | SENT to {user_email}")
            _update_streak(sub, self.db)
            _record_analytics(self.db, sub, module)
            self.repo.advance_module(sub)
        else:
            logger.error(f"LEARNING | {tag} | FAILED to {user_email}")
            self.repo.mark_sent(sub)

        return sent
