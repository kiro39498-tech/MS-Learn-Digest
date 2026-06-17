"""
Learning Curriculum Seeder — Enhanced batch version.

Handles the expanded curriculum with phase, skill_level, and milestone fields.
Idempotent — safe to call multiple times (ON CONFLICT DO NOTHING / DO UPDATE).
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
    Uses PostgreSQL ON CONFLICT for idempotency.
    Returns total new module rows inserted.
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
            set_={
                "total_modules": len(modules_data),
                "description": topic_data.get("description", ""),
                "difficulty_range": topic_data.get("difficulty_range"),
                "estimated_hours": topic_data.get("estimated_hours"),
            },
        )
        db.execute(topic_stmt)
        db.flush()

        topic = db.query(LearningTopic).filter(LearningTopic.slug == slug).first()
        if not topic:
            logger.error(f"SEED | topic not found after upsert: {slug}")
            continue

        # ── Batch-upsert modules ──────────────────────────────────────────
        module_rows = []
        for mod in modules_data:
            row = {
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
                # Enhanced fields
                "phase_name": mod.get("phase_name", ""),
                "phase_number": mod.get("phase_number", 1),
                "is_milestone": mod.get("is_milestone", False),
                "skill_level": mod.get("skill_level", mod.get("difficulty", "beginner")),
            }
            module_rows.append(row)

        if module_rows:
            mod_stmt = pg_insert(LearningModule).values(module_rows).on_conflict_do_update(
                index_elements=["topic_id", "sequence_number"],
                set_={
                    "title": pg_insert(LearningModule).excluded.title,
                    "description": pg_insert(LearningModule).excluded.description,
                    "learning_objectives": pg_insert(LearningModule).excluded.learning_objectives,
                    "keywords": pg_insert(LearningModule).excluded.keywords,
                    "estimated_duration_minutes": pg_insert(LearningModule).excluded.estimated_duration_minutes,
                    "difficulty_level": pg_insert(LearningModule).excluded.difficulty_level,
                    "phase_name": pg_insert(LearningModule).excluded.phase_name,
                    "phase_number": pg_insert(LearningModule).excluded.phase_number,
                    "is_milestone": pg_insert(LearningModule).excluded.is_milestone,
                    "skill_level": pg_insert(LearningModule).excluded.skill_level,
                },
            )
            result = db.execute(mod_stmt)
            inserted += result.rowcount or 0

    db.commit()
    logger.info(f"SEED | curriculum complete — {inserted} module rows inserted/updated.")
    return inserted
