"""
Topic model — hierarchical taxonomy.

Topics form a tree via the self-referential parent_topic_id FK.
Root topics have parent_topic_id = NULL and level = 0.

Subscription resolution: subscribing to a parent automatically includes
all descendant content via resolve_descendant_ids() in TopicRepository.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, func, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY, TEXT
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(TEXT)
    icon = Column(String(50))
    is_system = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # ── Hierarchy ──────────────────────────────────────────────────────────
    parent_topic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    level = Column(Integer, nullable=False, default=0)   # 0 = root, 1 = child, 2 = grandchild …

    # Catalog filter arrays — matched against catalog_cache.products_json / subjects_json
    catalog_products = Column(ARRAY(TEXT))
    catalog_subjects = Column(ARRAY(TEXT))

    created_at = Column(DateTime, default=func.now())

    # ── Relationships ──────────────────────────────────────────────────────
    # Self-referential tree:
    #   parent → this.parent_topic_id → parent row
    #   children → rows where parent_topic_id = this.id
    parent = relationship(
        "Topic",
        foreign_keys="Topic.parent_topic_id",
        back_populates="children",
        remote_side="[Topic.id]",
        lazy="select",
    )
    children = relationship(
        "Topic",
        foreign_keys="Topic.parent_topic_id",
        back_populates="parent",
        lazy="select",
    )

    user_subscriptions = relationship(
        "UserSubscription",
        back_populates="topic",
        cascade="all, delete-orphan",
    )
    newsletter_topics = relationship(
        "NewsletterTopic",
        back_populates="topic",
        cascade="all, delete-orphan",
    )


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "topic_id", name="_user_topic_uc"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="subscriptions")
    topic = relationship("Topic", back_populates="user_subscriptions")
