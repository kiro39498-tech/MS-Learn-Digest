"""
Learning Repository — Database access layer for the Learning Engine.

Completely separate from DigestRepository and TopicRepository.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.learning import (
    LearningTopic, LearningModule,
    UserLearningSubscription, GeneratedLesson,
)

logger = logging.getLogger(__name__)


_FREQUENCY_DELTA = {
    "daily":    timedelta(hours=20),
    "weekly":   timedelta(days=6),
    "biweekly": timedelta(days=13),
}


class LearningRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Topic queries ─────────────────────────────────────────────────────

    def get_all_topics(self) -> List[LearningTopic]:
        return (
            self.db.query(LearningTopic)
            .filter(LearningTopic.is_active == True)  # noqa: E712
            .order_by(LearningTopic.name)
            .all()
        )

    def get_topic_by_id(self, topic_id: UUID) -> Optional[LearningTopic]:
        return self.db.query(LearningTopic).filter(LearningTopic.id == topic_id).first()

    def get_topic_by_slug(self, slug: str) -> Optional[LearningTopic]:
        return self.db.query(LearningTopic).filter(LearningTopic.slug == slug).first()

    # ── Module queries ────────────────────────────────────────────────────

    def get_module(self, topic_id: UUID, sequence: int) -> Optional[LearningModule]:
        return (
            self.db.query(LearningModule)
            .filter(
                LearningModule.topic_id == topic_id,
                LearningModule.sequence_number == sequence,
                LearningModule.is_active == True,  # noqa: E712
            )
            .first()
        )

    def get_module_by_id(self, module_id: UUID) -> Optional[LearningModule]:
        return self.db.query(LearningModule).filter(LearningModule.id == module_id).first()

    def get_modules_for_topic(self, topic_id: UUID) -> List[LearningModule]:
        return (
            self.db.query(LearningModule)
            .filter(LearningModule.topic_id == topic_id, LearningModule.is_active == True)  # noqa: E712
            .order_by(LearningModule.sequence_number)
            .all()
        )

    # ── Subscription management ───────────────────────────────────────────

    def get_subscription(self, user_id: UUID, topic_id: UUID) -> Optional[UserLearningSubscription]:
        from sqlalchemy.orm import joinedload
        return (
            self.db.query(UserLearningSubscription)
            .options(joinedload(UserLearningSubscription.topic))
            .filter(
                UserLearningSubscription.user_id == user_id,
                UserLearningSubscription.topic_id == topic_id,
            )
            .first()
        )

    def get_user_subscriptions(self, user_id: UUID) -> List[UserLearningSubscription]:
        from sqlalchemy.orm import joinedload
        return (
            self.db.query(UserLearningSubscription)
            .options(joinedload(UserLearningSubscription.topic))
            .filter(UserLearningSubscription.user_id == user_id)
            .order_by(UserLearningSubscription.created_at)
            .all()
        )

    def create_subscription(
        self, user_id: UUID, topic_id: UUID, frequency: str
    ) -> UserLearningSubscription:
        sub = UserLearningSubscription(
            user_id=user_id,
            topic_id=topic_id,
            frequency=frequency,
            current_module_sequence=1,
            status="active",
        )
        self.db.add(sub)
        self.db.commit()
        # Re-query with topic eager-loaded so callers can access sub.topic
        from sqlalchemy.orm import joinedload
        return (
            self.db.query(UserLearningSubscription)
            .options(joinedload(UserLearningSubscription.topic))
            .filter(UserLearningSubscription.id == sub.id)
            .first()
        )

    def update_subscription_frequency(
        self, sub: UserLearningSubscription, frequency: str
    ) -> UserLearningSubscription:
        sub.frequency = frequency
        self.db.commit()
        from sqlalchemy.orm import joinedload
        return (
            self.db.query(UserLearningSubscription)
            .options(joinedload(UserLearningSubscription.topic))
            .filter(UserLearningSubscription.id == sub.id)
            .first()
        )

    def delete_subscription(self, user_id: UUID, topic_id: UUID) -> bool:
        deleted = (
            self.db.query(UserLearningSubscription)
            .filter(
                UserLearningSubscription.user_id == user_id,
                UserLearningSubscription.topic_id == topic_id,
            )
            .delete()
        )
        self.db.commit()
        return deleted > 0

    def advance_module(self, sub: UserLearningSubscription) -> None:
        """Move to next module; mark completed if last module reached."""
        topic = self.get_topic_by_id(sub.topic_id)
        next_seq = sub.current_module_sequence + 1
        if topic and next_seq > topic.total_modules:
            sub.status = "completed"
            sub.completed_at = datetime.now(timezone.utc)
        else:
            sub.current_module_sequence = next_seq
        sub.last_sent_at = datetime.now(timezone.utc)
        self.db.commit()

    def mark_sent(self, sub: UserLearningSubscription) -> None:
        sub.last_sent_at = datetime.now(timezone.utc)
        self.db.commit()

    def is_due(self, sub: UserLearningSubscription) -> bool:
        """Return True if the subscription is due for its next lesson."""
        if sub.status != "active":
            return False
        if sub.last_sent_at is None:
            return True
        delta = _FREQUENCY_DELTA.get(sub.frequency, timedelta(days=7))
        return datetime.now(timezone.utc) >= sub.last_sent_at + delta

    def get_all_due_subscriptions(self) -> List[UserLearningSubscription]:
        """Return all active subscriptions that are due for delivery, with user eager-loaded."""
        from sqlalchemy.orm import joinedload
        subs = (
            self.db.query(UserLearningSubscription)
            .options(joinedload(UserLearningSubscription.user))
            .filter(UserLearningSubscription.status == "active")
            .all()
        )
        return [s for s in subs if self.is_due(s)]

    # ── Generated lesson cache ────────────────────────────────────────────

    def get_generated_lesson(self, module_id: UUID) -> Optional[GeneratedLesson]:
        return (
            self.db.query(GeneratedLesson)
            .filter(GeneratedLesson.module_id == module_id)
            .first()
        )

    def save_generated_lesson(
        self,
        topic_id: UUID,
        module_id: UUID,
        generated_content: str,
        content_json: dict,
        resource_links: list,
        model: str,
    ) -> GeneratedLesson:
        lesson = GeneratedLesson(
            topic_id=topic_id,
            module_id=module_id,
            generated_content=generated_content,
            content_json=content_json,
            resource_links=resource_links,
            generation_model=model,
        )
        self.db.add(lesson)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson
