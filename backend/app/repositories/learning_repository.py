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
        """
        Move to next module in the user's active module list.
        Phase-aware: skips modules outside selected phases for custom tracks.
        Marks completed when no more modules remain.
        """
        active_modules = self.get_modules_for_subscription(sub)
        current_seqs = [m.sequence_number for m in active_modules]

        if not current_seqs:
            sub.status = "completed"
            sub.completed_at = datetime.now(timezone.utc)
            sub.last_sent_at = datetime.now(timezone.utc)
            self.db.commit()
            return

        current_idx = None
        for i, seq in enumerate(current_seqs):
            if seq == sub.current_module_sequence:
                current_idx = i
                break

        if current_idx is None or current_idx + 1 >= len(current_seqs):
            # No next module — completed
            sub.status = "completed"
            sub.completed_at = datetime.now(timezone.utc)
        else:
            sub.current_module_sequence = current_seqs[current_idx + 1]

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

    # ── Analytics queries ─────────────────────────────────────────────────

    def get_user_analytics(self, user_id: UUID, days: int = 30) -> dict:
        """Return learning metrics for a user over the last N days."""
        from datetime import timedelta
        from sqlalchemy import func
        from app.models.learning import LearningAnalytics

        since = datetime.now(timezone.utc) - timedelta(days=days)
        rows = (
            self.db.query(LearningAnalytics)
            .filter(
                LearningAnalytics.user_id == user_id,
                LearningAnalytics.sent_at >= since,
            )
            .all()
        )

        lessons_by_topic: dict = {}
        milestones_hit = 0
        for r in rows:
            topic_id_str = str(r.topic_id)
            lessons_by_topic[topic_id_str] = lessons_by_topic.get(topic_id_str, 0) + 1
            if r.is_milestone:
                milestones_hit += 1

        subs = self.get_user_subscriptions(user_id)
        longest_streak = max((s.longest_streak_days or 0 for s in subs), default=0)
        current_streak = max((s.current_streak_days or 0 for s in subs), default=0)
        total_sent = sum(s.total_lessons_sent or 0 for s in subs)

        return {
            "lessons_last_30_days": len(rows),
            "total_lessons_sent": total_sent,
            "milestones_completed": milestones_hit,
            "current_streak_days": current_streak,
            "longest_streak_days": longest_streak,
            "lessons_by_topic": lessons_by_topic,
            "active_tracks": sum(1 for s in subs if s.status == "active"),
            "completed_tracks": sum(1 for s in subs if s.status == "completed"),
        }

    # ── Phase subscriptions ───────────────────────────────────────────────

    def create_phase_subscriptions(
        self,
        sub: UserLearningSubscription,
        phase_names: list[str],
    ) -> int:
        """
        Set the selected phases for a custom (non-full-track) subscription.
        Replaces any existing phase selections for this subscription.
        Returns count of phase rows inserted.
        """
        from app.models.learning import UserPhaseSubscription

        # Delete existing phase selections for this subscription
        self.db.query(UserPhaseSubscription).filter(
            UserPhaseSubscription.subscription_id == sub.id
        ).delete()

        # Get unique phases with their phase_numbers from modules
        phases = (
            self.db.query(LearningModule.phase_name, LearningModule.phase_number)
            .filter(
                LearningModule.topic_id == sub.topic_id,
                LearningModule.phase_name.in_(phase_names),
                LearningModule.is_active == True,  # noqa: E712
            )
            .distinct()
            .all()
        )

        inserted = 0
        for phase_name, phase_number in phases:
            import uuid as _uuid
            row = UserPhaseSubscription(
                id=_uuid.uuid4(),
                user_id=sub.user_id,
                subscription_id=sub.id,
                topic_id=sub.topic_id,
                phase_name=phase_name,
                phase_number=phase_number,
                is_active=True,
            )
            self.db.add(row)
            inserted += 1

        self.db.commit()
        return inserted

    def get_subscribed_phases(self, sub: UserLearningSubscription) -> list[str]:
        """
        Return the list of selected phase names for a custom subscription.
        Returns [] if is_full_track = True (all phases active).
        """
        if sub.is_full_track:
            return []

        from app.models.learning import UserPhaseSubscription
        rows = (
            self.db.query(UserPhaseSubscription.phase_name)
            .filter(
                UserPhaseSubscription.subscription_id == sub.id,
                UserPhaseSubscription.is_active == True,  # noqa: E712
            )
            .order_by(UserPhaseSubscription.phase_number)
            .all()
        )
        return [r.phase_name for r in rows]

    def get_modules_for_subscription(self, sub: UserLearningSubscription) -> list[LearningModule]:
        """
        Return the ordered list of modules the user will receive.

        Full-track: all active modules in sequence order.
        Custom phases: only modules belonging to selected phases, in sequence order.
        """
        query = (
            self.db.query(LearningModule)
            .filter(
                LearningModule.topic_id == sub.topic_id,
                LearningModule.is_active == True,  # noqa: E712
            )
        )

        if not sub.is_full_track:
            selected_phases = self.get_subscribed_phases(sub)
            if selected_phases:
                query = query.filter(LearningModule.phase_name.in_(selected_phases))

        return query.order_by(LearningModule.sequence_number).all()
