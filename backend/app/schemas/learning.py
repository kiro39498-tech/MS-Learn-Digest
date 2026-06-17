"""
Learning Engine Pydantic Schemas
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class LearningTopicResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    total_modules: int
    difficulty_range: Optional[str] = None
    estimated_hours: Optional[int] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class LearningModuleResponse(BaseModel):
    id: UUID
    topic_id: UUID
    sequence_number: int
    title: str
    description: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    estimated_duration_minutes: Optional[int] = None
    difficulty_level: str
    phase_name: Optional[str] = None
    phase_number: int = 1
    is_milestone: bool = False
    skill_level: str = "beginner"

    model_config = ConfigDict(from_attributes=True)


class SubscribeRequest(BaseModel):
    topic_id: UUID
    frequency: str = "weekly"   # daily | weekly | biweekly


class UpdateFrequencyRequest(BaseModel):
    frequency: str


class LearningSubscriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    topic_id: UUID
    frequency: str
    current_module_sequence: int
    last_sent_at: Optional[datetime] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    # Nested topic info
    topic: LearningTopicResponse
    # Current module (may be None if completed)
    current_module: Optional[LearningModuleResponse] = None
    # Progress as percentage
    progress_pct: int = 0

    model_config = ConfigDict(from_attributes=True)


class LearningProgressResponse(BaseModel):
    topic_id: UUID
    topic_name: str
    topic_icon: Optional[str] = None
    current_module_sequence: int
    total_modules: int
    progress_pct: int
    status: str
    frequency: str
    skill_level: str = "beginner"
    current_streak_days: int = 0
    longest_streak_days: int = 0
    total_lessons_sent: int = 0
    last_sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    modules_completed: int
    modules_remaining: int
    # Current phase info
    current_phase_name: Optional[str] = None
    current_phase_number: int = 1


class LearningAnalyticsResponse(BaseModel):
    lessons_last_30_days: int
    total_lessons_sent: int
    milestones_completed: int
    current_streak_days: int
    longest_streak_days: int
    lessons_by_topic: dict
    active_tracks: int
    completed_tracks: int
