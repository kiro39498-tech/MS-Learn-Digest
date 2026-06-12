"""
Learning Track Models — Structured Progressive Learning Engine

These models are completely independent from the digest/catalog system.
They represent the Learning Engine's data layer.

Tables:
  LearningTopic               — a curriculum topic (Azure, Fabric, etc.)
  LearningModule              — one lesson within a topic, in sequence order
  UserLearningSubscription    — a user's enrollment in a topic + progress state
  GeneratedLesson             — cached AI-generated lesson content (shared across users)
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
    """
    A structured learning curriculum (e.g. "Azure", "Microsoft Fabric").

    Each topic has an ordered list of modules that form its curriculum.
    Users subscribe to topics — not to individual modules.
    """
    __tablename__ = "learning_topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    total_modules = Column(Integer, nullable=False, default=0)
    difficulty_range = Column(String(100), nullable=True)   # "Beginner → Advanced"
    estimated_hours = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
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
    """
    One lesson within a learning topic curriculum.

    Modules are ordered by sequence_number (1, 2, 3, …).
    Difficulty progresses from beginner to advanced across the sequence.
    """
    __tablename__ = "learning_modules"
    __table_args__ = (
        UniqueConstraint("topic_id", "sequence_number", name="uq_module_topic_seq"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    learning_objectives = Column(ARRAY(Text), nullable=True)
    keywords = Column(ARRAY(Text), nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    difficulty_level = Column(
        String(50), nullable=False, default="beginner"
    )  # beginner | intermediate | advanced
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    topic = relationship("LearningTopic", back_populates="modules")
    generated_lesson = relationship(
        "GeneratedLesson",
        back_populates="module",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserLearningSubscription(Base):
    """
    A user's enrollment in a learning topic.

    Tracks which module they're on and when they last received an email.
    Each subscription progresses independently — subscribing to Azure and
    Fabric results in two completely separate email streams.
    """
    __tablename__ = "user_learning_subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_user_learning_topic"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    frequency = Column(String(50), nullable=False, default="weekly")  # daily | weekly | biweekly
    current_module_sequence = Column(Integer, nullable=False, default=1)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="active")  # active | completed | paused
    created_at = Column(DateTime(timezone=True), default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    topic = relationship("LearningTopic", back_populates="subscriptions")


class GeneratedLesson(Base):
    """
    AI-generated lesson content for one module.

    Generated once per module and reused for all users.
    This eliminates redundant Groq calls — the cost is paid once regardless
    of how many users are enrolled in the same topic.
    """
    __tablename__ = "generated_lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_modules.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    generated_content = Column(Text, nullable=False)   # full rendered HTML
    content_json = Column(JSONB, nullable=True)         # structured Groq output
    resource_links = Column(JSONB, nullable=True)       # [{title, url, source}]
    generation_model = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    topic = relationship("LearningTopic")
    module = relationship("LearningModule", back_populates="generated_lesson")
