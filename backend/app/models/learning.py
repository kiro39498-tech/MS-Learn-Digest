"""
Learning Track Models — Enhanced Professional Learning Platform

Tables:
  LearningTopic            — curriculum topic with metadata
  LearningModule           — ordered lesson with phase/milestone/skill_level
  UserLearningSubscription — enrollment with streak + analytics counters
  GeneratedLesson          — cached AI lesson (reused across users)
  LearningAnalytics        — per-delivery audit log for dashboard metrics
  LearningWeeklyReview     — cached weekly summary emails
"""

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text, ForeignKey,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class LearningTopic(Base):
    __tablename__ = "learning_topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    total_modules = Column(Integer, nullable=False, default=0)
    difficulty_range = Column(String(100), nullable=True)
    estimated_hours = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    modules = relationship(
        "LearningModule",
        back_populates="topic",
        order_by="LearningModule.sequence_number",
        cascade="all, delete-orphan",
    )
    subscriptions = relationship(
        "UserLearningSubscription",
        back_populates="topic",
        cascade="all, delete-orphan",
    )


class LearningModule(Base):
    __tablename__ = "learning_modules"
    __table_args__ = (
        UniqueConstraint("topic_id", "sequence_number", name="uq_module_topic_seq"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_topics.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    sequence_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    learning_objectives = Column(ARRAY(Text), nullable=True)
    keywords = Column(ARRAY(Text), nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)

    # Original field kept for compat
    difficulty_level = Column(String(50), nullable=False, default="beginner")

    # Enhanced fields (added in migration g7h8i9j0k1l2)
    phase_name = Column(String(200), nullable=True)      # "Phase 1: Fundamentals"
    phase_number = Column(Integer, nullable=False, default=1)
    is_milestone = Column(Boolean, nullable=False, default=False)  # capstone/project
    skill_level = Column(String(50), nullable=False, default="beginner")
    # beginner | intermediate | advanced | expert

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    topic = relationship("LearningTopic", back_populates="modules")
    generated_lesson = relationship(
        "GeneratedLesson",
        back_populates="module",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserLearningSubscription(Base):
    __tablename__ = "user_learning_subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_user_learning_topic"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    topic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_topics.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    frequency = Column(String(50), nullable=False, default="weekly")
    current_module_sequence = Column(Integer, nullable=False, default=1)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Enhanced analytics fields (migration g7h8i9j0k1l2)
    skill_level = Column(String(50), nullable=False, default="beginner")
    current_streak_days = Column(Integer, nullable=False, default=0)
    longest_streak_days = Column(Integer, nullable=False, default=0)
    total_lessons_sent = Column(Integer, nullable=False, default=0)
    total_quiz_questions = Column(Integer, nullable=False, default=0)

    # Phase selection (migration h8i9j0k1l2m3)
    is_full_track = Column(Boolean, nullable=False, default=True)

    user = relationship("User")
    topic = relationship("LearningTopic", back_populates="subscriptions")
    analytics = relationship(
        "LearningAnalytics",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )
    phase_subscriptions = relationship(
        "UserPhaseSubscription",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )


class GeneratedLesson(Base):
    __tablename__ = "generated_lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_topics.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_modules.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    generated_content = Column(Text, nullable=False)
    content_json = Column(JSONB, nullable=True)
    resource_links = Column(JSONB, nullable=True)
    generation_model = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    topic = relationship("LearningTopic")
    module = relationship("LearningModule", back_populates="generated_lesson")


class LearningAnalytics(Base):
    """Per-delivery audit log. Used to power dashboard metrics."""
    __tablename__ = "learning_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_learning_subscriptions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    topic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_modules.id", ondelete="CASCADE"),
        nullable=False,
    )
    module_sequence = Column(Integer, nullable=False)
    sent_at = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    difficulty_level = Column(String(50), nullable=True)
    phase_name = Column(String(200), nullable=True)
    is_milestone = Column(Boolean, nullable=False, default=False)

    subscription = relationship("UserLearningSubscription", back_populates="analytics")


class LearningWeeklyReview(Base):
    """Cached weekly summary email sent every Sunday."""
    __tablename__ = "learning_weekly_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    week_start = Column(DateTime(timezone=True), nullable=False, index=True)
    week_end = Column(DateTime(timezone=True), nullable=False)
    lessons_completed = Column(Integer, nullable=False, default=0)
    topics_covered = Column(ARRAY(Text), nullable=True)
    content_html = Column(Text, nullable=False, default="")
    content_json = Column(JSONB, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())


class UserPhaseSubscription(Base):
    """
    Records which specific phases a user has chosen within a track.
    Only populated when UserLearningSubscription.is_full_track = False.

    When is_full_track = True, this table has no rows for that subscription
    and the learning engine delivers all phases in sequence.
    """
    __tablename__ = "user_phase_subscriptions"
    __table_args__ = (
        UniqueConstraint("subscription_id", "phase_name", name="uq_phase_sub_phase"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_learning_subscriptions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    topic_id = Column(
        UUID(as_uuid=True), ForeignKey("learning_topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    phase_name = Column(String(200), nullable=False)
    phase_number = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    subscription = relationship("UserLearningSubscription",
                                back_populates="phase_subscriptions")
