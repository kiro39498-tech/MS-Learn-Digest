"""Catalog cache refactor

Replaces the full content warehouse (content, content_ai, content_changes,
content_details, content_topics) with a single lightweight catalog_cache table.

digest_items is migrated non-destructively:
  - New columns (uid, title, url, content_type) are added first.
  - Existing rows are backfilled from the content table while it still exists.
  - The content_id FK is dropped after backfill.
  - The old content-warehouse tables are then dropped in FK order.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-04 14:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Step 1: Add new columns to digest_items ───────────────────────────
    op.add_column("digest_items", sa.Column("uid", sa.Text(), nullable=True))
    op.add_column("digest_items", sa.Column("title", sa.Text(), nullable=True))
    op.add_column("digest_items", sa.Column("url", sa.Text(), nullable=True))
    op.add_column("digest_items", sa.Column("content_type", sa.String(100), nullable=True))

    # ── Step 2: Backfill from content table (runs while content still exists) ─
    op.execute("""
        UPDATE digest_items di
        SET
            uid          = c.uid,
            title        = c.title,
            url          = c.url,
            content_type = c.content_type
        FROM content c
        WHERE di.content_id = c.id
          AND di.content_id IS NOT NULL
    """)

    # ── Step 3: Drop FK constraint on digest_items.content_id ────────────
    # PostgreSQL auto-names constraints; use IF EXISTS for safety across envs
    op.execute("""
        DO $$
        DECLARE
            constraint_name TEXT;
        BEGIN
            SELECT conname INTO constraint_name
            FROM pg_constraint
            WHERE conrelid = 'digest_items'::regclass
              AND contype = 'f'
              AND conname LIKE '%content%';
            IF constraint_name IS NOT NULL THEN
                EXECUTE 'ALTER TABLE digest_items DROP CONSTRAINT ' || constraint_name;
            END IF;
        END $$;
    """)

    # ── Step 4: Drop content_id column from digest_items ─────────────────
    op.drop_column("digest_items", "content_id")

    # ── Step 5: Drop dependent tables in FK order ─────────────────────────
    # content_changes → content
    op.drop_table("content_changes")

    # content_ai → content
    op.drop_table("content_ai")

    # content_details → content
    op.drop_table("content_details")

    # content_topics → content, topics
    op.drop_index("ix_content_uid", table_name="content")
    op.drop_table("content_topics")

    # ── Step 6: Drop content table ────────────────────────────────────────
    op.drop_table("content")

    # ── Step 7: Create catalog_cache ──────────────────────────────────────
    op.create_table(
        "catalog_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uid", sa.String(500), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("products_json", postgresql.JSONB(astext_type=sa.Text()),
                  nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("subjects_json", postgresql.JSONB(astext_type=sa.Text()),
                  nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_catalog_cache_uid", "catalog_cache", ["uid"], unique=True)
    op.create_index("ix_catalog_cache_last_modified", "catalog_cache", ["last_modified"])


def downgrade() -> None:
    # ── Reverse Step 7: Drop catalog_cache ───────────────────────────────
    op.drop_index("ix_catalog_cache_last_modified", table_name="catalog_cache")
    op.drop_index("ix_catalog_cache_uid", table_name="catalog_cache")
    op.drop_table("catalog_cache")

    # ── Reverse Step 6: Re-create content ────────────────────────────────
    op.create_table(
        "content",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uid", sa.String(500), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("levels", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("roles", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("products", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("subjects", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("icon_url", sa.Text(), nullable=True),
        sa.Column("popularity", sa.Float(), nullable=True),
        sa.Column("locale", sa.String(20), nullable=True),
        sa.Column("last_modified", sa.DateTime(), nullable=True),
        sa.Column("first_seen", sa.DateTime(), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("is_new", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_uid", "content", ["uid"], unique=True)

    # ── Reverse Step 5: Re-create dependent tables ────────────────────────
    op.create_table(
        "content_topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_id", "topic_id", name="_content_topic_uc"),
    )
    op.create_table(
        "content_details",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("learning_objectives", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("prerequisites", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("unit_titles", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("scraped_summary", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("scrape_status", sa.String(50), nullable=True),
        sa.Column("scraped_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_id"),
    )
    op.create_table(
        "content_ai",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("classified_topics", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("audience", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("difficulty", sa.String(50), nullable=True),
        sa.Column("why_it_matters", sa.Text(), nullable=True),
        sa.Column("key_takeaways", postgresql.ARRAY(sa.TEXT()), nullable=True),
        sa.Column("recommended_audience", sa.Text(), nullable=True),
        sa.Column("newsletter_summary", sa.Text(), nullable=True),
        sa.Column("ai_model", sa.String(100), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_id"),
    )
    op.create_table(
        "content_changes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("change_type", sa.String(20), nullable=False),
        sa.Column("change_detected_at", sa.DateTime(), nullable=False),
        sa.Column("previous_modified_date", sa.DateTime(), nullable=True),
        sa.Column("current_modified_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── Reverse Step 4 & 3: Restore content_id column with FK ────────────
    op.add_column(
        "digest_items",
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "digest_items_content_id_fkey",
        "digest_items", "content",
        ["content_id"], ["id"],
        ondelete="SET NULL",
    )

    # ── Reverse Step 1: Drop new columns ─────────────────────────────────
    op.drop_column("digest_items", "content_type")
    op.drop_column("digest_items", "url")
    op.drop_column("digest_items", "title")
    op.drop_column("digest_items", "uid")
