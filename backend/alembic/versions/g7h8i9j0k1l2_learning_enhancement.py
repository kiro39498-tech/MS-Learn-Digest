"""Learning tracks enhancement

Adds learning paths, phases, analytics, weekly reviews, and milestone projects
to the existing learning engine.

New columns on learning_modules:
  - phase_name       : learning path phase (e.g. "Phase 1: Fundamentals")
  - phase_number     : integer ordering of phase within a topic
  - is_milestone     : True for project/capstone modules
  - skill_level      : beginner | intermediate | advanced | expert
  - interview_questions_count : how many interview Qs to generate

New tables:
  - learning_analytics : per-subscription lesson delivery tracking
  - learning_weekly_reviews : cached weekly review emails

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-15 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "g7h8i9j0k1l2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Enhance learning_modules ───────────────────────────────────────
    op.add_column("learning_modules",
        sa.Column("phase_name", sa.String(200), nullable=True))
    op.add_column("learning_modules",
        sa.Column("phase_number", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("learning_modules",
        sa.Column("is_milestone", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("learning_modules",
        sa.Column("skill_level", sa.String(50), nullable=False, server_default="'beginner'"))

    # ── 2. Enhance user_learning_subscriptions ────────────────────────────
    op.add_column("user_learning_subscriptions",
        sa.Column("skill_level", sa.String(50), nullable=False, server_default="'beginner'"))
    op.add_column("user_learning_subscriptions",
        sa.Column("current_streak_days", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("user_learning_subscriptions",
        sa.Column("longest_streak_days", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("user_learning_subscriptions",
        sa.Column("total_lessons_sent", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("user_learning_subscriptions",
        sa.Column("total_quiz_questions", sa.Integer(), nullable=False, server_default="0"))

    # ── 3. Create learning_analytics ──────────────────────────────────────
    op.create_table(
        "learning_analytics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_sequence", sa.Integer(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("difficulty_level", sa.String(50), nullable=True),
        sa.Column("phase_name", sa.String(200), nullable=True),
        sa.Column("is_milestone", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["subscription_id"], ["user_learning_subscriptions.id"],
                                ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["learning_topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["learning_modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_la_user_id", "learning_analytics", ["user_id"])
    op.create_index("ix_la_subscription_id", "learning_analytics", ["subscription_id"])
    op.create_index("ix_la_sent_at", "learning_analytics", ["sent_at"])

    # ── 4. Create learning_weekly_reviews ─────────────────────────────────
    op.create_table(
        "learning_weekly_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("week_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("week_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lessons_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("topics_covered", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("content_html", sa.Text(), nullable=False, server_default="''"),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lwr_user_id", "learning_weekly_reviews", ["user_id"])
    op.create_index("ix_lwr_week_start", "learning_weekly_reviews", ["week_start"])


def downgrade() -> None:
    op.drop_index("ix_lwr_week_start", table_name="learning_weekly_reviews")
    op.drop_index("ix_lwr_user_id", table_name="learning_weekly_reviews")
    op.drop_table("learning_weekly_reviews")
    op.drop_index("ix_la_sent_at", table_name="learning_analytics")
    op.drop_index("ix_la_subscription_id", table_name="learning_analytics")
    op.drop_index("ix_la_user_id", table_name="learning_analytics")
    op.drop_table("learning_analytics")
    op.drop_column("user_learning_subscriptions", "total_quiz_questions")
    op.drop_column("user_learning_subscriptions", "total_lessons_sent")
    op.drop_column("user_learning_subscriptions", "longest_streak_days")
    op.drop_column("user_learning_subscriptions", "current_streak_days")
    op.drop_column("user_learning_subscriptions", "skill_level")
    op.drop_column("learning_modules", "skill_level")
    op.drop_column("learning_modules", "is_milestone")
    op.drop_column("learning_modules", "phase_number")
    op.drop_column("learning_modules", "phase_name")
