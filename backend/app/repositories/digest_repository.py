"""
Digest Repository — Persistence layer for digests and digest items.

digest_items no longer holds a FK to a content table.
uid / title / url / content_type are stored inline.
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload

from app.models.digest import Digest, DigestItem

logger = logging.getLogger(__name__)


class DigestRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Digest creation ───────────────────────────────────────────────────

    def create_digest(
        self,
        title: str,
        digest_type: str,
        content_html: str,
        content_json: dict,
        topic_names: List[str],
        period_start: datetime,
        period_end: datetime,
        user_id: Optional[UUID] = None,
        team_id: Optional[UUID] = None,
        newsletter_id: Optional[UUID] = None,
        status: str = "generated",
    ) -> Digest:
        digest = Digest(
            title=title,
            digest_type=digest_type,
            content_html=content_html,
            content_json=content_json,
            topic_names=topic_names,
            period_start=period_start,
            period_end=period_end,
            user_id=user_id,
            team_id=team_id,
            newsletter_id=newsletter_id,
            status=status,
        )
        self.db.add(digest)
        self.db.flush()   # populate id before adding items
        return digest

    def add_item(
        self,
        digest_id: UUID,
        uid: str,
        title: str,
        url: str,
        content_type: str,
        position: int,
        section: str = "ms_learn_updates",
    ) -> DigestItem:
        item = DigestItem(
            digest_id=digest_id,
            uid=uid,
            title=title,
            url=url,
            content_type=content_type,
            position=position,
            section=section,
        )
        self.db.add(item)
        return item

    # ── Status updates ────────────────────────────────────────────────────

    def mark_sent(self, digest_id: UUID, recipient_count: int) -> None:
        digest = self.db.query(Digest).filter(Digest.id == digest_id).first()
        if digest:
            digest.status = "sent"
            digest.sent_at = datetime.now(timezone.utc)
            digest.recipient_count = recipient_count
            self.db.commit()

    def mark_failed(self, digest_id: UUID) -> None:
        digest = self.db.query(Digest).filter(Digest.id == digest_id).first()
        if digest:
            digest.status = "failed"
            self.db.commit()

    # ── History queries ───────────────────────────────────────────────────

    def get_user_digests(self, user_id: UUID, limit: int = 20) -> List[Digest]:
        return (
            self.db.query(Digest)
            .options(joinedload(Digest.items))
            .filter(Digest.user_id == user_id)
            .order_by(Digest.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_digest_by_id(self, digest_id: UUID, user_id: UUID) -> Optional[Digest]:
        return (
            self.db.query(Digest)
            .options(joinedload(Digest.items))
            .filter(Digest.id == digest_id, Digest.user_id == user_id)
            .first()
        )
