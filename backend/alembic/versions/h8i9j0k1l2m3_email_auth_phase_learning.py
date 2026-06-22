"""Email authentication + phase-based learning subscriptions

Feature 1 — Email Auth:
  Adds to users table:
    auth_provider   : 'google' | 'email'
    email_verified  : bool
    last_login      : timestamptz

  Creates email_login_tokens table for magic-link auth:
    id, user_id (nullable — for new users), email, token (hashed),
    expires_at, used_at, created_at

Feature 2 — Phase-based learning:
  Adds to user_learning_subscriptions:
    is_full_track   : bool  (True = whole track, False = selected phases)

  Creates user_phase_subscriptions table:
    id, user_id, subscription_id, topic_id, phase_name, phase_number,
    is_active, created_at

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-06-18 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "h8i9j0k1l2m3"
down_revision: Union[str, Sequence[str], None] = "g7h8i9j0k1l2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Enhance users table ─────────────────────────────────────────────
    # Make google_id nullable so email-only users don't need it
    op.alter_column("users", "google_id", nullable=True)
    op.add_column("users",
        sa.Column("auth_provider", sa.String(50), nullable=False, server_default="'google'"))
    op.add_column("users",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users",
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True))

    # ── 2. Create email_login_tokens ───────────────────────────────────────
    op.create_table(
        "email_login_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("token_hash", sa.String(256), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_email_token_hash"),
    )
    op.create_index("ix_elt_email", "email_login_tokens", ["email"])
    op.create_index("ix_elt_token_hash", "email_login_tokens", ["token_hash"])
    op.create_index("ix_elt_expires_at", "email_login_tokens", ["expires_at"])

    # ── 3. Add is_full_track to user_learning_subscriptions ───────────────
    op.add_column("user_learning_subscriptions",
        sa.Column("is_full_track", sa.Boolean(), nullable=False, server_default="true"))

    # ── 4. Create user_phase_subscriptions ────────────────────────────────
    op.create_table(
        "user_phase_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phase_name", sa.String(200), nullable=False),
        sa.Column("phase_number", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"],
                                ["user_learning_subscriptions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["learning_topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subscription_id", "phase_name",
                            name="uq_phase_sub_phase"),
    )
    op.create_index("ix_ups_user_id", "user_phase_subscriptions", ["user_id"])
    op.create_index("ix_ups_subscription_id", "user_phase_subscriptions", ["subscription_id"])

    # ── 5. Mark existing google users as verified ──────────────────────────
    op.execute("""
        UPDATE users
        SET auth_provider = 'google',
            email_verified = true
        WHERE google_id IS NOT NULL AND google_id != ''
    """)


def downgrade() -> None:
    op.drop_index("ix_ups_subscription_id", table_name="user_phase_subscriptions")
    op.drop_index("ix_ups_user_id", table_name="user_phase_subscriptions")
    op.drop_table("user_phase_subscriptions")
    op.drop_column("user_learning_subscriptions", "is_full_track")
    op.drop_index("ix_elt_expires_at", table_name="email_login_tokens")
    op.drop_index("ix_elt_token_hash", table_name="email_login_tokens")
    op.drop_index("ix_elt_email", table_name="email_login_tokens")
    op.drop_table("email_login_tokens")
    op.drop_column("users", "last_login")
    op.drop_column("users", "email_verified")
    op.drop_column("users", "auth_provider")
    op.alter_column("users", "google_id", nullable=False)
