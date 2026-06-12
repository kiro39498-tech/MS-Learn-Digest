"""
Topic schemas — tree-aware Pydantic models.

TopicNode is the recursive tree shape returned by GET /api/topics/tree.
TopicFlat is the flat shape returned by GET /api/topics/ (used by dropdowns).
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class TopicFlat(BaseModel):
    """Flat topic record — used in dropdowns, subscription lists, etc."""
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_system: bool = True
    is_active: bool = True
    parent_topic_id: Optional[UUID] = None
    level: int = 0
    catalog_products: Optional[List[str]] = None
    catalog_subjects: Optional[List[str]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Keep backward-compat alias so existing code that imports TopicResponse still works
TopicResponse = TopicFlat


class TopicNode(BaseModel):
    """
    Recursive tree node — used by GET /api/topics/tree.
    children are nested TopicNode objects.

    NOTE: We deliberately do NOT use from_attributes=True here because
    reading the SQLAlchemy children relationship would pre-populate
    children, and then _build_tree() would duplicate them by appending again.
    TopicNode instances are always constructed manually in _build_tree().
    """
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True
    parent_topic_id: Optional[UUID] = None
    level: int = 0
    catalog_products: Optional[List[str]] = None
    catalog_subjects: Optional[List[str]] = None
    children: List["TopicNode"] = []


TopicNode.model_rebuild()   # required for self-referential models


class UserSubscriptionCreate(BaseModel):
    topic_ids: List[UUID]


class UserSubscriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    topic_id: UUID
    created_at: datetime
    topic: TopicFlat

    model_config = ConfigDict(from_attributes=True)
