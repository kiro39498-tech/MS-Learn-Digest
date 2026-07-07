"""Microsoft Learn MCP enrichment cache

Adds a daily cache for Learning-only MCP documentation enrichment and records
the MCP metadata used by generated lesson rows.

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-07-07 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, Sequence[str], None] = "h8i9j0k1l2m3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("generated_lessons",
                  sa.Column("documentation_hash", sa.String(64), nullable=True))
    op.add_column("generated_lessons",
                  sa.Column("mcp_summary", sa.Text(), nullable=True))
    op.add_column("generated_lessons",
                  sa.Column("code_sample_links",
                            postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("generated_lessons",
                  sa.Column("mcp_cache_date", sa.Date(), nullable=True))
    op.add_column("generated_lessons",
                  sa.Column("mcp_last_updated", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "mcp_documentation_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.String(500), nullable=False),
        sa.Column("cache_date", sa.Date(), nullable=False),
        sa.Column("documentation_hash", sa.String(64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("documentation_links", postgresql.JSONB(astext_type=sa.Text()),
                  nullable=True),
        sa.Column("code_sample_links", postgresql.JSONB(astext_type=sa.Text()),
                  nullable=True),
        sa.Column("best_practices", postgresql.JSONB(astext_type=sa.Text()),
                  nullable=True),
        sa.Column("source_status", sa.String(50), nullable=False,
                  server_default="success"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("topic", "cache_date", name="uq_mcp_doc_topic_date"),
    )
    op.create_index("ix_mcp_documentation_cache_topic",
                    "mcp_documentation_cache", ["topic"])
    op.create_index("ix_mcp_documentation_cache_cache_date",
                    "mcp_documentation_cache", ["cache_date"])
    op.create_index("ix_mcp_documentation_cache_expires_at",
                    "mcp_documentation_cache", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_mcp_documentation_cache_expires_at",
                  table_name="mcp_documentation_cache")
    op.drop_index("ix_mcp_documentation_cache_cache_date",
                  table_name="mcp_documentation_cache")
    op.drop_index("ix_mcp_documentation_cache_topic",
                  table_name="mcp_documentation_cache")
    op.drop_table("mcp_documentation_cache")

    op.drop_column("generated_lessons", "mcp_last_updated")
    op.drop_column("generated_lessons", "mcp_cache_date")
    op.drop_column("generated_lessons", "code_sample_links")
    op.drop_column("generated_lessons", "mcp_summary")
    op.drop_column("generated_lessons", "documentation_hash")
