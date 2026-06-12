"""
Topics API — Hierarchical topic taxonomy, subscriptions, and onboarding.

Endpoints
─────────
GET  /api/topics/          — flat list of all active topics (all levels)
GET  /api/topics/tree      — full topic tree (nested children)
GET  /api/topics/roots     — root topics only (level 0)
GET  /api/topics/my        — topics the current user is subscribed to (flat)
POST /api/topics/subscribe — replace user subscriptions (accepts any level)
POST /api/topics/onboard   — finish onboarding wizard (save topics + mark flag)

Subscription semantics
──────────────────────
Users may subscribe at any level.  Subscribing to a parent (e.g. "Azure")
does NOT auto-subscribe to children in the subscriptions table — it simply
means the digest generator will resolve descendants at generation time via
TopicRepository.resolve_descendant_ids().  This keeps the subscription
table clean while still delivering parent-aware content.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.topic_repository import TopicRepository
from app.repositories.user_repository import UserRepository
from app.schemas.topic import (
    TopicFlat, TopicNode, TopicResponse,
    UserSubscriptionCreate, UserSubscriptionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_tree(topics: List) -> List[TopicNode]:
    """
    Build a nested tree from a flat list of Topic ORM objects.

    We convert each ORM object to a TopicNode with children=[] explicitly
    (ignoring the SQLAlchemy relationship) and then manually attach children
    based on parent_topic_id. This avoids double-population that occurs when
    Pydantic's from_attributes eagerly reads the SQLAlchemy children
    relationship AND we also append children manually.
    """
    # Build nodes with empty children lists — do NOT let Pydantic read the
    # SQLAlchemy .children relationship (that would pre-populate them).
    nodes: dict = {}
    for t in topics:
        node = TopicNode(
            id=t.id,
            name=t.name,
            slug=t.slug,
            description=t.description,
            icon=t.icon,
            is_active=t.is_active,
            parent_topic_id=t.parent_topic_id,
            level=t.level,
            catalog_products=t.catalog_products,
            catalog_subjects=t.catalog_subjects,
            children=[],   # always start empty
        )
        nodes[t.id] = node

    roots = []
    for node in nodes.values():
        if node.parent_topic_id is None:
            roots.append(node)
        else:
            parent = nodes.get(node.parent_topic_id)
            if parent is not None:
                parent.children.append(node)
            else:
                # Parent not in the result set (e.g. inactive) — treat as root
                roots.append(node)

    roots.sort(key=lambda n: n.name)
    for node in nodes.values():
        node.children.sort(key=lambda n: n.name)
    return roots


# ── Topic list endpoints ───────────────────────────────────────────────────────

@router.get("/", response_model=List[TopicFlat])
async def list_topics(db: Session = Depends(get_db)):
    """Flat list of all active topics, ordered by level then name."""
    repo = TopicRepository(db)
    topics = repo.get_all()
    if not topics:
        repo.seed_system_topics()
        topics = repo.get_all()
    return topics


@router.get("/tree", response_model=List[TopicNode])
async def get_topic_tree(db: Session = Depends(get_db)):
    """
    Full nested topic tree.
    Root topics contain a 'children' array of sub-topics (recursive).
    """
    repo = TopicRepository(db)
    topics = repo.get_all()
    if not topics:
        repo.seed_system_topics()
        topics = repo.get_all()
    return _build_tree(topics)


@router.get("/roots", response_model=List[TopicFlat])
async def get_root_topics(db: Session = Depends(get_db)):
    """Root-level topics only (level = 0)."""
    repo = TopicRepository(db)
    roots = repo.get_roots()
    if not roots:
        repo.seed_system_topics()
        roots = repo.get_roots()
    return roots


@router.get("/{topic_id}/children", response_model=List[TopicFlat])
async def get_topic_children(
    topic_id: UUID,
    db: Session = Depends(get_db),
):
    """Direct children of a specific topic."""
    repo = TopicRepository(db)
    topic = repo.get_by_id(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return repo.get_children(topic_id)


# ── User subscription endpoints ────────────────────────────────────────────────

@router.get("/my", response_model=List[TopicFlat])
async def get_my_subscriptions(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Return the topics the current user is explicitly subscribed to (flat list).
    Also self-heals is_onboarded if subscriptions exist but flag is False.
    """
    uid = UUID(user_id)
    topic_repo = TopicRepository(db)
    user_repo = UserRepository(db)

    user_repo.ensure_onboarded_if_subscribed(uid)
    subs = topic_repo.get_user_subscriptions(uid)
    return [s.topic for s in subs]


@router.post("/subscribe", response_model=List[UserSubscriptionResponse])
async def subscribe_topics(
    payload: UserSubscriptionCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Replace the user's explicit topic subscriptions.
    Accepts topic IDs at any hierarchy level.
    Automatically marks the user as onboarded once they have ≥1 subscription.
    """
    uid = UUID(user_id)
    topic_repo = TopicRepository(db)
    user_repo = UserRepository(db)

    subs = topic_repo.replace_user_subscriptions(uid, payload.topic_ids)

    if payload.topic_ids:
        healed = user_repo.ensure_onboarded_if_subscribed(uid)
        if healed:
            logger.info(
                f"SUBSCRIBE | user_id={user_id} | "
                f"auto-set is_onboarded=True after saving {len(payload.topic_ids)} topics"
            )

    result = []
    for sub in subs:
        db.refresh(sub)
        result.append(sub)
    return result


@router.post("/onboard")
async def complete_onboarding(
    payload: UserSubscriptionCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Called at the end of the Onboarding wizard.
    Saves topic subscriptions and explicitly marks the user as onboarded.
    """
    uid = UUID(user_id)
    topic_repo = TopicRepository(db)
    user_repo = UserRepository(db)

    if payload.topic_ids:
        topic_repo.replace_user_subscriptions(uid, payload.topic_ids)

    user = user_repo.mark_onboarded(uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"ONBOARD | user_id={user_id} | topics={len(payload.topic_ids)} | is_onboarded=True")
    return {"status": "onboarded", "is_onboarded": True}
