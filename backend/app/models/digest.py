"""
Digest models.

DigestItem stores uid/title/url/content_type directly — no FK to a content table.
This makes digest history self-contained and independent of any catalog storage.
"""

from sqlalchemy import Column, String, DateTime, func, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Digest(Base):
    __tablename__ = "digests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    digest_type = Column(String(50), nullable=False)   # 'individual' | 'team'
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    newsletter_id = Column(UUID(as_uuid=True), ForeignKey("team_newsletters.id", ondelete="SET NULL"), nullable=True)
    content_html = Column(Text, nullable=False)
    content_json = Column(JSONB)
    topic_names = Column(ARRAY(String), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="generated")   # 'generated' | 'sent' | 'failed'
    recipient_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=func.now())

    user = relationship("User", back_populates="digests")
    team = relationship("Team", back_populates="digests")
    newsletter = relationship("TeamNewsletter", back_populates="digests")
    items = relationship("DigestItem", back_populates="digest", cascade="all, delete-orphan")


class DigestItem(Base):
    """
    One content item inside a digest.

    Stores catalog metadata directly so digest history is self-contained —
    no dependency on the catalog_cache or any content table.
    """
    __tablename__ = "digest_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    digest_id = Column(UUID(as_uuid=True), ForeignKey("digests.id", ondelete="CASCADE"), nullable=False)

    # Catalog metadata stored inline — no FK to catalog_cache
    uid = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    content_type = Column(String(100), nullable=True)

    position = Column(Integer, nullable=True)
    section = Column(String(100), nullable=True)   # always 'ms_learn_updates'
    created_at = Column(DateTime(timezone=True), default=func.now())

    digest = relationship("Digest", back_populates="items")
