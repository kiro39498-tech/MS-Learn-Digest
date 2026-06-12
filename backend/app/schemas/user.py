from pydantic import BaseModel, EmailStr, ConfigDict, field_serializer
from typing import Optional
from uuid import UUID
from datetime import datetime, time

class UserPreferenceBase(BaseModel):
    frequency: str = "weekly"
    delivery_time: time = time(8, 0)
    delivery_day: int = 0
    timezone: str = "UTC"

class UserPreferenceCreate(UserPreferenceBase):
    pass

class UserPreferenceResponse(UserPreferenceBase):
    id: UUID
    user_id: UUID

    # Serialize delivery_time as "HH:MM" (not the full "HH:MM:SS") so the
    # frontend can safely split on ":" to get hours and minutes.
    @field_serializer("delivery_time")
    def serialize_delivery_time(self, v: time) -> str:
        return v.strftime("%H:%M")

    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: EmailStr
    name: str
    avatar_url: Optional[str] = None
    role: str = "individual"
    is_onboarded: bool = False

class UserCreate(UserBase):
    google_id: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_onboarded: Optional[bool] = None

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    preferences: Optional[UserPreferenceResponse] = None

    model_config = ConfigDict(from_attributes=True)
