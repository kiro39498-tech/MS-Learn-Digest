"""Hierarchical topic system

Adds parent_topic_id, level, and is_active to the topics table.
Existing flat topics become level-0 root nodes (parent_topic_id = NULL).
All existing topics are marked is_active = TRUE.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-12 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Step 1: Add new columns to topics ─────────────────────────────────
    op.add_column(
        "topics",
        sa.Column(
            "parent_topic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "topics",
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "topics",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )

    # ── Step 2: Index on parent_topic_id for recursive lookups ────────────
    op.create_index(
        "ix_topics_parent_topic_id",
        "topics",
        ["parent_topic_id"],
    )

    # ── Step 3: Backfill — all existing topics are root-level ─────────────
    op.execute("UPDATE topics SET level = 0, is_active = true WHERE parent_topic_id IS NULL")


def downgrade() -> None:
    op.drop_index("ix_topics_parent_topic_id", table_name="topics")
    op.drop_column("topics", "is_active")
    op.drop_column("topics", "level")
    op.drop_column("topics", "parent_topic_id")
