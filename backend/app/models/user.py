from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # google_id is nullable — email-only users won't have one
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    avatar_url = Column(String)
    role = Column(String(50), default="individual")  # 'individual' | 'admin'
    is_onboarded = Column(Boolean, default=False)

    # Auth provider fields (migration h8i9j0k1l2m3)
    auth_provider = Column(String(50), nullable=False, default="google")  # 'google' | 'email'
    email_verified = Column(Boolean, nullable=False, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    preferences = relationship("UserPreference", back_populates="user",
                               uselist=False, cascade="all, delete-orphan")
    subscriptions = relationship("UserSubscription", back_populates="user",
                                 cascade="all, delete-orphan")
    teams_owned = relationship("Team", back_populates="admin",
                               cascade="all, delete-orphan")
    team_memberships = relationship("TeamMember", back_populates="user",
                                   cascade="all, delete-orphan")
    digests = relationship("Digest", back_populates="user")
