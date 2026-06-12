from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey, UniqueConstraint, Integer, Time, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(String)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    admin = relationship("User", back_populates="teams_owned")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    newsletters = relationship("TeamNewsletter", back_populates="team", cascade="all, delete-orphan")
    digests = relationship("Digest", back_populates="team")


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "email", name="_team_email_uc"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    email = Column(String(255), nullable=False)
    role = Column(String(50), default="member")  # 'admin' | 'member'
    # Status lifecycle: pending → accepted | declined | expired
    status = Column(String(50), default="pending")
    joined_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")
    invitations = relationship("TeamInvitation", back_populates="member", cascade="all, delete-orphan")


class TeamInvitation(Base):
    """
    Secure invitation token for a team member.
    One-time use, with expiration. Linked to a TeamMember row.
    """
    __tablename__ = "team_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey("team_members.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(256), unique=True, nullable=False, index=True)
    invited_by_email = Column(String(255), nullable=True)
    # status: 'pending' | 'accepted' | 'declined' | 'expired'
    status = Column(String(50), nullable=False, default="pending")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    team = relationship("Team")
    member = relationship("TeamMember", back_populates="invitations")


class TeamNewsletter(Base):
    __tablename__ = "team_newsletters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    frequency = Column(String(50), default="weekly")
    delivery_time = Column(Time, default="09:00:00")
    delivery_day = Column(Integer, default=0)  # 0=Mon
    timezone = Column(String(100), default="UTC")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    team = relationship("Team", back_populates="newsletters")
    topics = relationship("NewsletterTopic", back_populates="newsletter", cascade="all, delete-orphan")
    digests = relationship("Digest", back_populates="newsletter")


class NewsletterTopic(Base):
    __tablename__ = "newsletter_topics"
    __table_args__ = (UniqueConstraint("newsletter_id", "topic_id", name="_newsletter_topic_uc"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    newsletter_id = Column(UUID(as_uuid=True), ForeignKey("team_newsletters.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)

    newsletter = relationship("TeamNewsletter", back_populates="topics")
    topic = relationship("Topic", back_populates="newsletter_topics")


class SyncMetadata(Base):
    """
    Singleton table (id=1 always) storing the last catalog sync result.
    Used by the scheduler and admin UI to show sync health.
    """
    __tablename__ = "sync_metadata"

    id = Column(Integer, primary_key=True)
    last_sync_started_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_completed_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_fetched = Column(Integer, nullable=True)
    last_sync_upserted = Column(Integer, nullable=True)
    last_sync_status = Column(String(50), nullable=True)  # 'success' | 'failed'
