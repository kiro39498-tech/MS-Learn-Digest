"""
Users API — Profile and preferences management.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserPreferenceCreate, UserPreferenceResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get current authenticated user profile including preferences.
    Self-heals is_onboarded if the user has subscriptions but the flag is False.
    """
    repo = UserRepository(db)
    uid = UUID(user_id)

    # Self-heal before returning — fixes users who subscribed via Preferences page
    repo.ensure_onboarded_if_subscribed(uid)

    user = repo.get_by_id(uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/me/preferences", response_model=UserPreferenceResponse)
async def update_preferences(
    payload: UserPreferenceCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create or update the current user's delivery preferences."""
    repo = UserRepository(db)
    pref = repo.upsert_preferences(
        user_id=UUID(user_id),
        frequency=payload.frequency,
        delivery_day=payload.delivery_day,
        delivery_time=payload.delivery_time,
        timezone=payload.timezone,
    )
    return pref
