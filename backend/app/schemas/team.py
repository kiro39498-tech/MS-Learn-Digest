"""
Team Pydantic schemas.

Timezone is fixed to Asia/Kolkata across the entire application.
No timezone selection is exposed in any API or UI.
"""

from pydantic import BaseModel, EmailStr, ConfigDict, field_serializer, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime, time

# Fixed timezone — never ask the user for this
FIXED_TZ = "Asia/Kolkata"


# ── Topic helpers ─────────────────────────────────────────────────────────────

class NewsletterTopicResponse(BaseModel):
    id: UUID
    topic_id: UUID
    topic_name: Optional[str] = None
    topic_slug: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Newsletter response ────────────────────────────────────────────────────────

class TeamNewsletterResponse(BaseModel):
    id: UUID
    team_id: UUID
    name: str
    frequency: str
    delivery_time: str   # always "HH:MM"
    delivery_day: int
    timezone: str        # always "Asia/Kolkata"
    is_active: bool
    created_at: datetime
    updated_at: datetime
    topics: List[NewsletterTopicResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("delivery_time")
    def _ser_dt(self, v) -> str:
        if isinstance(v, time):
            return v.strftime("%H:%M")
        if v is None:
            return "09:00"
        return str(v)[:5]


# ── Newsletter update schemas ─────────────────────────────────────────────────

class UpdateTopicsRequest(BaseModel):
    topic_ids: List[UUID]


class UpdateScheduleRequest(BaseModel):
    """Only frequency, delivery_time, and delivery_day are editable. TZ is fixed."""
    frequency: str = "weekly"     # daily | weekly | biweekly | monthly
    delivery_time: str = "09:00"  # HH:MM
    delivery_day: int = 0         # 0=Mon … 6=Sun (ignored for monthly/daily)

    @field_validator("delivery_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        parts = v.split(":")
        if len(parts) < 2:
            raise ValueError("delivery_time must be HH:MM")
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("delivery_time out of range")
        return f"{h:02d}:{m:02d}"

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        valid = {"daily", "weekly", "biweekly", "monthly"}
        if v not in valid:
            raise ValueError(f"frequency must be one of {valid}")
        return v


# ── Team creation ──────────────────────────────────────────────────────────────

class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None
    topic_ids: List[UUID]
    frequency: str = "weekly"
    delivery_time: str = "09:00"
    delivery_day: int = 0
    # timezone intentionally omitted — always Asia/Kolkata

    @field_validator("delivery_time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        parts = v.split(":")
        if len(parts) < 2:
            raise ValueError("delivery_time must be HH:MM")
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# ── Invitations ───────────────────────────────────────────────────────────────

class TeamInvitationResponse(BaseModel):
    id: UUID
    team_id: UUID
    member_id: UUID
    email: str
    status: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvitePreviewResponse(BaseModel):
    team_id: UUID
    team_name: str
    team_description: Optional[str] = None
    invited_by_email: Optional[str] = None
    email: str
    status: str
    expires_at: datetime
    topics: List[str] = []
    frequency: Optional[str] = None
    schedule_label: Optional[str] = None


# ── Members ───────────────────────────────────────────────────────────────────

class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = "member"


class TeamMemberResponse(BaseModel):
    id: UUID
    team_id: UUID
    user_id: Optional[UUID] = None
    email: str
    role: str
    status: str   # pending | accepted | declined | expired | removed
    joined_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InviteResult(BaseModel):
    member: TeamMemberResponse
    invitation_token: str
    invitation_expires_at: datetime
    invite_url: str
    email_sent: bool


# ── Full team response ────────────────────────────────────────────────────────

class TeamResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    admin_id: UUID
    created_at: datetime
    updated_at: datetime
    members: List[TeamMemberResponse] = []
    newsletter: Optional[TeamNewsletterResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ── Digest history ────────────────────────────────────────────────────────────

class TeamDigestSummary(BaseModel):
    id: UUID
    title: str
    status: str
    recipient_count: int
    created_at: datetime
    sent_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
