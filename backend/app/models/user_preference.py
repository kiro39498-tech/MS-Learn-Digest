from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    frequency = Column(String(50), default="weekly") # 'daily', 'weekly', 'biweekly', 'monthly'
    delivery_time = Column(Time, default="08:00:00")
    delivery_day = Column(Integer, default=1) # 0=Mon, 6=Sun
    timezone = Column(String(100), default="UTC")

    user = relationship("User", back_populates="preferences")
