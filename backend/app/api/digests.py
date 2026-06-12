"""
Digests API — Retrieve digest history for the current user.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.digest_repository import DigestRepository
from app.schemas.digest import DigestResponse, DigestDetailResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[DigestResponse])
async def list_digests(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List the most recent 20 digests for the current user."""
    repo = DigestRepository(db)
    return repo.get_user_digests(UUID(user_id))


@router.get("/{digest_id}", response_model=DigestDetailResponse)
async def get_digest(
    digest_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get full digest content including rendered HTML."""
    repo = DigestRepository(db)
    digest = repo.get_digest_by_id(digest_id, UUID(user_id))
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    return digest
