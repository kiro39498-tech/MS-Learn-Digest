"""
Learning Curriculum Seeder — optimised batch version.

Uses bulk INSERT instead of per-row existence checks to avoid N+1 queries.
Safe to run multiple times (ON CONFLICT DO NOTHING via unique constraints).
"""

import logging
import uuid
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.models.learning import LearningTopic, LearningModule
from app.services.learning.curriculum import LEARNING_CURRICULUM

logger = logging.getLogger(__name__)


def seed_learning_curriculum(db: Session) -> int:
    """
    Upsert all learning topics and modules from curriculum.py.
    Uses PostgreSQL ON CONFLICT DO NOTHING for idempotency.
    Returns total rows inserted.
    """
    inserted = 0

    for topic_data in LEARNING_CURRICULUM:
        modules_data = topic_data.get("modules", [])
        slug = topic_data["slug"]

        # ── Upsert topic ──────────────────────────────────────────────────
        topic_stmt = pg_insert(LearningTopic).values(
            id=uuid.uuid4(),
            name=topic_data["name"],
            slug=slug,
            description=topic_data.get("description", ""),
            icon=topic_data.get("icon", "📚"),
            total_modules=len(modules_data),
            difficulty_range=topic_data.get("difficulty_range"),
            estimated_hours=topic_data.get("estimated_hours"),
            is_active=True,
        ).on_conflict_do_update(
            index_elements=["slug"],
            set_={"total_modules": len(modules_data)},   # keep total_modules in sync
        )
        db.execute(topic_stmt)
        db.flush()

        # Re-fetch the canonical topic id (may have existed before)
        topic = db.query(LearningTopic).filter(LearningTopic.slug == slug).first()
        if not topic:
            logger.error(f"SEED | topic not found after upsert: {slug}")
            continue

        # ── Batch-upsert modules ──────────────────────────────────────────
        module_rows = [
            {
                "id": uuid.uuid4(),
                "topic_id": topic.id,
                "sequence_number": mod["seq"],
                "title": mod["title"],
                "description": mod.get("description", ""),
                "learning_objectives": mod.get("objectives", []),
                "keywords": mod.get("keywords", []),
                "estimated_duration_minutes": mod.get("duration", 30),
                "difficulty_level": mod.get("difficulty", "beginner"),
                "is_active": True,
            }
            for mod in modules_data
        ]

        if module_rows:
            mod_stmt = pg_insert(LearningModule).values(module_rows).on_conflict_do_nothing(
                index_elements=["topic_id", "sequence_number"]
            )
            result = db.execute(mod_stmt)
            inserted += result.rowcount or 0

    db.commit()
    logger.info(f"SEED | learning curriculum complete — {inserted} new module rows inserted.")
    return inserted
