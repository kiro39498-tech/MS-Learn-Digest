"""
User Repository — Database access layer for users and preferences.
"""

import logging
from typing import Optional
from uuid import UUID
from datetime import time
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.topic import UserSubscription

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def subscription_count(self, user_id: UUID) -> int:
        """Return how many topic subscriptions the user has."""
        return (
            self.db.query(UserSubscription)
            .filter(UserSubscription.user_id == user_id)
            .count()
        )

    def mark_onboarded(self, user_id: UUID) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            user.is_onboarded = True
            self.db.commit()
            self.db.refresh(user)
        return user

    def ensure_onboarded_if_subscribed(self, user_id: UUID) -> bool:
        """
        Self-healing: if the user has ≥1 subscription but is_onboarded is False,
        flip the flag automatically.  Returns True if the flag was changed.
        """
        user = self.get_by_id(user_id)
        if user and not user.is_onboarded:
            count = self.subscription_count(user_id)
            if count > 0:
                user.is_onboarded = True
                self.db.commit()
                self.db.refresh(user)
                logger.info(
                    f"AUTO-HEAL | user={user.email} | "
                    f"set is_onboarded=True (had {count} subscriptions)"
                )
                return True
        return False

    def upsert_preferences(
        self,
        user_id: UUID,
        frequency: str,
        delivery_day: int,
        delivery_time: time,
        timezone: str,
    ) -> UserPreference:
        pref = (
            self.db.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .first()
        )
        if pref:
            pref.frequency = frequency
            pref.delivery_day = delivery_day
            pref.delivery_time = delivery_time
            pref.timezone = timezone
        else:
            pref = UserPreference(
                user_id=user_id,
                frequency=frequency,
                delivery_day=delivery_day,
                delivery_time=delivery_time,
                timezone=timezone,
            )
            self.db.add(pref)
        self.db.commit()
        self.db.refresh(pref)
        return pref
