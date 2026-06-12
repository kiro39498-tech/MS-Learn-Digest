from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class DigestItemResponse(BaseModel):
    id: UUID
    position: Optional[int] = None
    section: Optional[str] = None
    uid: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    content_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DigestBase(BaseModel):
    title: str
    digest_type: str


class DigestResponse(DigestBase):
    id: UUID
    user_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    newsletter_id: Optional[UUID] = None
    topic_names: List[str] = []
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    status: str
    recipient_count: int
    created_at: datetime
    items: List[DigestItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DigestDetailResponse(DigestResponse):
    content_html: str
    content_json: Any
