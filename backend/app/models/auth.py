"""
Auth models — email magic-link token storage.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class EmailLoginToken(Base):
    """
    Single-use, time-limited token for magic-link email authentication.

    Flow:
      1. User requests login with their email.
      2. A random token is generated, hashed (SHA-256), and stored here.
      3. The raw token is emailed as a URL parameter.
      4. On verification: hash incoming token, look up in DB,
         check expiry, mark used, return JWT.
    """
    __tablename__ = "email_login_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    token_hash = Column(String(256), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
