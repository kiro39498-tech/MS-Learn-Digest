"""Team invitations and member status upgrade

Adds team_invitations table and sync_metadata table.
Updates team_members.status from ('invited','active') to
('pending','accepted','declined','expired').

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-08 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Migrate team_members.status values ────────────────────────────
    op.execute("""
        UPDATE team_members
        SET status = CASE
            WHEN status = 'active'  THEN 'accepted'
            WHEN status = 'invited' THEN 'pending'
            ELSE status
        END
    """)

    # ── 2. Create team_invitations table ─────────────────────────────────
    op.create_table(
        "team_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("token", sa.String(256), nullable=False),
        sa.Column("invited_by_email", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False,
                  server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["team_members.id"],
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_team_invitations_token"),
    )
    op.create_index("ix_team_invitations_token", "team_invitations",
                    ["token"], unique=True)
    op.create_index("ix_team_invitations_email", "team_invitations", ["email"])

    # ── 3. Create sync_metadata singleton table ───────────────────────────
    op.create_table(
        "sync_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("last_sync_started_at", sa.DateTime(timezone=True),
                  nullable=True),
        sa.Column("last_sync_completed_at", sa.DateTime(timezone=True),
                  nullable=True),
        sa.Column("last_sync_fetched", sa.Integer(), nullable=True),
        sa.Column("last_sync_upserted", sa.Integer(), nullable=True),
        sa.Column("last_sync_status", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("INSERT INTO sync_metadata (id) VALUES (1)")


def downgrade() -> None:
    op.drop_table("sync_metadata")
    op.drop_index("ix_team_invitations_email",
                  table_name="team_invitations")
    op.drop_index("ix_team_invitations_token",
                  table_name="team_invitations")
    op.drop_table("team_invitations")
    op.execute("""
        UPDATE team_members
        SET status = CASE
            WHEN status = 'accepted' THEN 'active'
            WHEN status = 'pending'  THEN 'invited'
            ELSE status
        END
    """)
