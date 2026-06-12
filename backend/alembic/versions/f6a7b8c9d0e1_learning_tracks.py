"""Learning Tracks — structured progressive learning engine

Creates four new tables that are completely independent from the
existing digest/catalog system:

  learning_topics           — predefined curriculum topics with module counts
  learning_modules          — ordered lesson definitions per topic
  user_learning_subscriptions — per-user subscription with progress tracking
  generated_lessons         — cached AI-generated lesson content (reused across users)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-12 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. learning_topics ────────────────────────────────────────────────
    op.create_table(
        "learning_topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("total_modules", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("difficulty_range", sa.String(100), nullable=True),   # e.g. "Beginner → Advanced"
        sa.Column("estimated_hours", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_learning_topics_slug"),
        sa.UniqueConstraint("name", name="uq_learning_topics_name"),
    )
    op.create_index("ix_learning_topics_slug", "learning_topics", ["slug"], unique=True)

    # ── 2. learning_modules ───────────────────────────────────────────────
    op.create_table(
        "learning_modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),   # 1-based ordering
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("learning_objectives", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("difficulty_level", sa.String(50), nullable=False,
                  server_default="'beginner'"),   # beginner | intermediate | advanced
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["topic_id"], ["learning_topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("topic_id", "sequence_number", name="uq_module_topic_seq"),
    )
    op.create_index("ix_learning_modules_topic_id", "learning_modules", ["topic_id"])
    op.create_index("ix_learning_modules_seq", "learning_modules",
                    ["topic_id", "sequence_number"])

    # ── 3. user_learning_subscriptions ───────────────────────────────────
    op.create_table(
        "user_learning_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("frequency", sa.String(50), nullable=False,
                  server_default="'weekly'"),   # daily | weekly | biweekly
        sa.Column("current_module_sequence", sa.Integer(), nullable=False,
                  server_default="1"),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False,
                  server_default="'active'"),   # active | completed | paused
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["learning_topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "topic_id", name="uq_user_learning_topic"),
    )
    op.create_index("ix_uls_user_id", "user_learning_subscriptions", ["user_id"])
    op.create_index("ix_uls_topic_id", "user_learning_subscriptions", ["topic_id"])
    op.create_index("ix_uls_status", "user_learning_subscriptions", ["status"])

    # ── 4. generated_lessons ─────────────────────────────────────────────
    op.create_table(
        "generated_lessons",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("generated_content", sa.Text(), nullable=False),   # full HTML lesson
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()),
                  nullable=True),   # structured JSON from Groq
        sa.Column("resource_links", postgresql.JSONB(astext_type=sa.Text()),
                  nullable=True),   # [{title, url, source}]
        sa.Column("generation_model", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["topic_id"], ["learning_topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["learning_modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_id", name="uq_generated_lesson_module"),
    )
    op.create_index("ix_generated_lessons_module_id", "generated_lessons", ["module_id"],
                    unique=True)
    op.create_index("ix_generated_lessons_topic_id", "generated_lessons", ["topic_id"])


def downgrade() -> None:
    op.drop_index("ix_generated_lessons_topic_id", table_name="generated_lessons")
    op.drop_index("ix_generated_lessons_module_id", table_name="generated_lessons")
    op.drop_table("generated_lessons")
    op.drop_index("ix_uls_status", table_name="user_learning_subscriptions")
    op.drop_index("ix_uls_topic_id", table_name="user_learning_subscriptions")
    op.drop_index("ix_uls_user_id", table_name="user_learning_subscriptions")
    op.drop_table("user_learning_subscriptions")
    op.drop_index("ix_learning_modules_seq", table_name="learning_modules")
    op.drop_index("ix_learning_modules_topic_id", table_name="learning_modules")
    op.drop_table("learning_modules")
    op.drop_index("ix_learning_topics_slug", table_name="learning_topics")
    op.drop_table("learning_topics")
