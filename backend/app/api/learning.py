"""
Learning Tracks API

Completely independent from the digest/newsletter API.
Handles topic browsing, enrollment, phase selection, and progress tracking.

Endpoints
─────────
GET  /api/learning/topics                       — all available learning topics
GET  /api/learning/topics/{topic_id}            — single topic with modules
GET  /api/learning/topics/{topic_id}/phases     — distinct phases for a topic
POST /api/learning/subscribe                    — subscribe (full track or custom phases)
DELETE /api/learning/subscribe/{topic_id}       — unsubscribe
PATCH /api/learning/subscribe/{topic_id}/phases — update selected phases
PATCH /api/learning/subscribe/{topic_id}/frequency
GET  /api/learning/my                           — active subscriptions + progress
GET  /api/learning/progress/{topic_id}          — detailed progress for one topic
GET  /api/learning/completed                    — completed tracks
GET  /api/learning/analytics                    — learning metrics
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.learning_repository import LearningRepository
from app.schemas.learning import (
    LearningTopicResponse, LearningModuleResponse,
    LearningProgressResponse, LearningAnalyticsResponse,
    SubscribeRequest, UpdateFrequencyRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request schemas ───────────────────────────────────────────────────────────

class PhaseSubscribeRequest(BaseModel):
    """
    Unified subscribe request that supports both full-track and phase-specific enrollment.

    is_full_track = True  → deliver all phases in sequence (existing behaviour)
    is_full_track = False → deliver only the phases listed in selected_phases
    """
    topic_id: UUID
    frequency: str = "weekly"
    is_full_track: bool = True
    selected_phases: List[str] = []   # phase_name values; ignored when is_full_track=True


class UpdatePhasesRequest(BaseModel):
    is_full_track: bool = True
    selected_phases: List[str] = []


def _to_progress(sub, repo: LearningRepository) -> LearningProgressResponse:
    topic = sub.topic
    current_mod = repo.get_module(sub.topic_id, sub.current_module_sequence)

    # For phase-based subs, total = modules in selected phases only
    if sub.is_full_track:
        active_modules = repo.get_modules_for_topic(sub.topic_id)
    else:
        active_modules = repo.get_modules_for_subscription(sub)

    total = len(active_modules) or 1
    active_seqs = [m.sequence_number for m in active_modules]
    completed_count = sum(1 for s in active_seqs if s < sub.current_module_sequence)
    pct = min(100, int((completed_count / total) * 100))

    selected_phases = [] if sub.is_full_track else repo.get_subscribed_phases(sub)

    return LearningProgressResponse(
        topic_id=sub.topic_id,
        topic_name=topic.name,
        topic_icon=topic.icon,
        current_module_sequence=sub.current_module_sequence,
        total_modules=total,
        progress_pct=pct,
        status=sub.status,
        frequency=sub.frequency,
        skill_level=getattr(sub, "skill_level", "beginner"),
        current_streak_days=getattr(sub, "current_streak_days", 0) or 0,
        longest_streak_days=getattr(sub, "longest_streak_days", 0) or 0,
        total_lessons_sent=getattr(sub, "total_lessons_sent", 0) or 0,
        last_sent_at=sub.last_sent_at,
        completed_at=sub.completed_at,
        modules_completed=completed_count,
        modules_remaining=max(0, total - completed_count),
        current_phase_name=getattr(current_mod, "phase_name", None) if current_mod else None,
        current_phase_number=getattr(current_mod, "phase_number", 1) if current_mod else 1,
        is_full_track=getattr(sub, "is_full_track", True),
        selected_phases=selected_phases,
    )


# ── Topic browsing ─────────────────────────────────────────────────────────────

@router.get("/topics", response_model=List[LearningTopicResponse])
async def list_learning_topics(db: Session = Depends(get_db)):
    """All available learning track topics."""
    repo = LearningRepository(db)
    try:
        topics = repo.get_all_topics()
        if not topics:
            from app.services.learning.seeder import seed_learning_curriculum
            seed_learning_curriculum(db)
            topics = repo.get_all_topics()
        return topics
    except Exception as exc:
        logger.warning(f"LEARNING | topics endpoint error (migration pending?): {exc}")
        return []


@router.get("/topics/{topic_id}", response_model=LearningTopicResponse)
async def get_learning_topic(topic_id: UUID, db: Session = Depends(get_db)):
    """Single topic details."""
    repo = LearningRepository(db)
    topic = repo.get_topic_by_id(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Learning topic not found")
    return topic


@router.get("/topics/{topic_id}/modules", response_model=List[LearningModuleResponse])
async def get_topic_modules(topic_id: UUID, db: Session = Depends(get_db)):
    """All modules for a learning topic in sequence order."""
    repo = LearningRepository(db)
    topic = repo.get_topic_by_id(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Learning topic not found")
    return repo.get_modules_for_topic(topic_id)


@router.get("/topics/{topic_id}/phases")
async def get_topic_phases(topic_id: UUID, db: Session = Depends(get_db)):
    """
    Return distinct phases for a topic with module counts and difficulty range.
    Used by the frontend phase-selection UI.
    """
    repo = LearningRepository(db)
    topic = repo.get_topic_by_id(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Learning topic not found")

    modules = repo.get_modules_for_topic(topic_id)
    phases_map: dict = {}
    for mod in modules:
        p = mod.phase_name or "General"
        pn = getattr(mod, "phase_number", 1)
        if p not in phases_map:
            phases_map[p] = {
                "phase_name": p,
                "phase_number": pn,
                "module_count": 0,
                "difficulty_levels": set(),
                "first_sequence": mod.sequence_number,
            }
        phases_map[p]["module_count"] += 1
        phases_map[p]["difficulty_levels"].add(mod.skill_level or mod.difficulty_level)

    phases = sorted(phases_map.values(), key=lambda x: x["phase_number"])
    return {
        "topic_id": str(topic_id),
        "topic_name": topic.name,
        "phases": [
            {
                "phase_name": p["phase_name"],
                "phase_number": p["phase_number"],
                "module_count": p["module_count"],
                "difficulty_levels": sorted(p["difficulty_levels"]),
            }
            for p in phases
        ],
    }
async def get_topic_modules(topic_id: UUID, db: Session = Depends(get_db)):
    """All modules for a learning topic in sequence order."""
    repo = LearningRepository(db)
    topic = repo.get_topic_by_id(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Learning topic not found")
    return repo.get_modules_for_topic(topic_id)


# ── Subscription management ────────────────────────────────────────────────────

@router.post("/subscribe", response_model=LearningProgressResponse)
async def subscribe_to_learning_track(
    payload: PhaseSubscribeRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Subscribe to a learning track — full track or selected phases.
    If already subscribed, updates frequency and phase selection.
    """
    uid = UUID(user_id)
    repo = LearningRepository(db)

    topic = repo.get_topic_by_id(payload.topic_id)
    if not topic or not topic.is_active:
        raise HTTPException(status_code=404, detail="Learning topic not found or inactive")

    valid_frequencies = {"daily", "weekly", "biweekly"}
    if payload.frequency not in valid_frequencies:
        raise HTTPException(
            status_code=422,
            detail=f"frequency must be one of: {sorted(valid_frequencies)}",
        )

    if not payload.is_full_track and not payload.selected_phases:
        raise HTTPException(
            status_code=422,
            detail="selected_phases must not be empty when is_full_track=False",
        )

    existing = repo.get_subscription(uid, payload.topic_id)
    if existing:
        existing.frequency = payload.frequency
        existing.is_full_track = payload.is_full_track
        db.commit()
        if not payload.is_full_track:
            repo.create_phase_subscriptions(existing, payload.selected_phases)
            # Reset to first module of first selected phase
            modules = repo.get_modules_for_subscription(existing)
            if modules:
                existing.current_module_sequence = modules[0].sequence_number
                existing.status = "active"
                existing.completed_at = None
                db.commit()
        logger.info(
            f"LEARNING | user={uid} topic={topic.name} | "
            f"updated freq={payload.frequency} full_track={payload.is_full_track}"
        )
        sub = repo.get_subscription(uid, payload.topic_id)
    else:
        # Create new subscription
        sub = repo.create_subscription(uid, payload.topic_id, payload.frequency)
        sub.is_full_track = payload.is_full_track
        db.commit()

        if not payload.is_full_track:
            repo.create_phase_subscriptions(sub, payload.selected_phases)
            modules = repo.get_modules_for_subscription(sub)
            if modules:
                sub.current_module_sequence = modules[0].sequence_number
                db.commit()

        logger.info(
            f"LEARNING | user={uid} topic={topic.name} | "
            f"NEW freq={payload.frequency} full_track={payload.is_full_track}"
        )
        sub = repo.get_subscription(uid, payload.topic_id)

    return _to_progress(sub, repo)


@router.patch("/subscribe/{topic_id}/phases", response_model=LearningProgressResponse)
async def update_phase_selection(
    topic_id: UUID,
    payload: UpdatePhasesRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update phase selection for an existing subscription."""
    uid = UUID(user_id)
    repo = LearningRepository(db)
    sub = repo.get_subscription(uid, topic_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if not payload.is_full_track and not payload.selected_phases:
        raise HTTPException(
            status_code=422,
            detail="selected_phases must not be empty when is_full_track=False",
        )

    sub.is_full_track = payload.is_full_track
    db.commit()

    if not payload.is_full_track:
        repo.create_phase_subscriptions(sub, payload.selected_phases)
        modules = repo.get_modules_for_subscription(sub)
        if modules and sub.current_module_sequence not in [m.sequence_number for m in modules]:
            sub.current_module_sequence = modules[0].sequence_number
            sub.status = "active"
            sub.completed_at = None
            db.commit()

    return _to_progress(repo.get_subscription(uid, topic_id), repo)


@router.delete("/subscribe/{topic_id}")
async def unsubscribe_from_learning_track(
    topic_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Unsubscribe from a learning track."""
    uid = UUID(user_id)
    repo = LearningRepository(db)
    deleted = repo.delete_subscription(uid, topic_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"status": "unsubscribed", "topic_id": str(topic_id)}


@router.patch("/subscribe/{topic_id}/frequency")
async def update_learning_frequency(
    topic_id: UUID,
    payload: UpdateFrequencyRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update delivery frequency for a learning track subscription."""
    uid = UUID(user_id)
    repo = LearningRepository(db)
    sub = repo.get_subscription(uid, topic_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    sub = repo.update_subscription_frequency(sub, payload.frequency)
    return _to_progress(sub, repo)


# ── Progress tracking ──────────────────────────────────────────────────────────

@router.get("/my", response_model=List[LearningProgressResponse])
async def get_my_learning_tracks(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """All active + completed learning subscriptions with progress."""
    uid = UUID(user_id)
    repo = LearningRepository(db)
    try:
        subs = repo.get_user_subscriptions(uid)
        return [_to_progress(s, repo) for s in subs]
    except Exception as exc:
        logger.warning(f"LEARNING | my endpoint error (migration pending?): {exc}")
        return []


@router.get("/progress/{topic_id}", response_model=LearningProgressResponse)
async def get_learning_progress(
    topic_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Detailed progress for a single learning track."""
    uid = UUID(user_id)
    repo = LearningRepository(db)
    sub = repo.get_subscription(uid, topic_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Not subscribed to this learning track")
    return _to_progress(sub, repo)


@router.get("/completed", response_model=List[LearningProgressResponse])
async def get_completed_tracks(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Completed learning tracks."""
    uid = UUID(user_id)
    repo = LearningRepository(db)
    subs = repo.get_user_subscriptions(uid)
    return [_to_progress(s, repo) for s in subs if s.status == "completed"]


@router.get("/analytics", response_model=LearningAnalyticsResponse)
async def get_learning_analytics(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Learning analytics and metrics for the current user."""
    uid = UUID(user_id)
    repo = LearningRepository(db)
    try:
        return repo.get_user_analytics(uid)
    except Exception as exc:
        logger.warning(f"LEARNING | analytics error: {exc}")
        return LearningAnalyticsResponse(
            lessons_last_30_days=0, total_lessons_sent=0,
            milestones_completed=0, current_streak_days=0,
            longest_streak_days=0, lessons_by_topic={},
            active_tracks=0, completed_tracks=0,
        )


# ── Status / seed endpoint (unauthenticated, for debugging) ───────────────────

@router.get("/status")
async def learning_engine_status(db: Session = Depends(get_db)):
    """
    Health check for the Learning Engine.
    Shows whether the DB tables exist, how many topics/modules are seeded,
    and triggers a seed if empty. Useful for diagnosing setup issues.
    """
    try:
        from app.services.learning.seeder import seed_learning_curriculum
        from sqlalchemy import text, func

        # Check if tables exist
        result = db.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name IN ('learning_topics','learning_modules',"
            "'user_learning_subscriptions','generated_lessons')"
        )).scalar()

        if result < 4:
            return {
                "status": "migration_pending",
                "message": "Learning track tables not found. Run: alembic upgrade head",
                "tables_found": result,
                "tables_needed": 4,
            }

        repo = LearningRepository(db)
        topic_count = db.execute(text("SELECT COUNT(*) FROM learning_topics")).scalar()
        module_count = db.execute(text("SELECT COUNT(*) FROM learning_modules")).scalar()

        seeded_now = 0
        if topic_count == 0:
            seeded_now = seed_learning_curriculum(db)
            topic_count = db.execute(text("SELECT COUNT(*) FROM learning_topics")).scalar()
            module_count = db.execute(text("SELECT COUNT(*) FROM learning_modules")).scalar()

        topics = repo.get_all_topics()
        return {
            "status": "ok",
            "tables": "all present",
            "topics": topic_count,
            "modules": module_count,
            "seeded_now": seeded_now,
            "topic_list": [
                {"name": t.name, "slug": t.slug, "modules": t.total_modules}
                for t in topics
            ],
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "fix": "Run: alembic upgrade head inside the backend container",
        }


@router.post("/seed")
async def seed_learning_topics(db: Session = Depends(get_db)):
    """
    Manually seed the learning curriculum.
    Safe to call multiple times (idempotent).
    """
    try:
        from app.services.learning.seeder import seed_learning_curriculum
        inserted = seed_learning_curriculum(db)
        repo = LearningRepository(db)
        topics = repo.get_all_topics()
        return {
            "status": "ok",
            "inserted": inserted,
            "total_topics": len(topics),
            "topics": [{"name": t.name, "modules": t.total_modules} for t in topics],
        }
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Seed failed: {exc}. Ensure migration has been applied: alembic upgrade head",
        )
