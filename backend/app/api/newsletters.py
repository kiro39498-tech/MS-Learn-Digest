"""
Newsletters API — Read-only convenience endpoints.

Newsletter creation/editing is now done through the Teams API
(one newsletter per team, created atomically with the team).
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.team_repository import TeamRepository
from app.schemas.team import TeamNewsletterResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[TeamNewsletterResponse])
async def list_my_newsletters(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List the newsletter for every team the current user administers."""
    team_repo = TeamRepository(db)
    teams = team_repo.get_teams_for_user(UUID(user_id))
    newsletters = []
    for team in teams:
        if str(team.admin_id) == user_id:
            nl = team_repo.get_newsletter(team.id)
            if nl:
                newsletters.append(nl)
    return newsletters
