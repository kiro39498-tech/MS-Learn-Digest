"""Add content_changes table for change-detection digest model

Revision ID: a1b2c3d4e5f6
Revises: 28e549d24050
Create Date: 2026-06-04 12:00:00.000000

This migration adds the content_changes table.
Every catalog sync writes one row per NEW or UPDATED item.
Digest generation queries this table within the user's frequency window
instead of scanning all 4,500+ content records.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "28e549d24050"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_changes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("content_id", sa.UUID(), nullable=False),
        sa.Column("change_type", sa.String(length=20), nullable=False),
        sa.Column("change_detected_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("previous_modified_date", sa.DateTime(), nullable=True),
        sa.Column("current_modified_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Index on content_id for FK lookups
    op.create_index(
        "ix_content_changes_content_id",
        "content_changes",
        ["content_id"],
    )
    # Index on change_detected_at — the primary filter in every digest query
    op.create_index(
        "ix_content_changes_detected_at",
        "content_changes",
        ["change_detected_at"],
    )
    # Composite index: the digest query always filters on detected_at + content_id
    op.create_index(
        "ix_content_changes_detected_content",
        "content_changes",
        ["change_detected_at", "content_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_content_changes_detected_content", table_name="content_changes")
    op.drop_index("ix_content_changes_detected_at", table_name="content_changes")
    op.drop_index("ix_content_changes_content_id", table_name="content_changes")
    op.drop_table("content_changes")
