"""Team one-newsletter refactor

Enforces one newsletter per team:
  - Removes duplicate newsletters (keeps the one with the earliest id).
  - Adds UNIQUE(team_id) on team_newsletters.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-08 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Remove duplicate newsletters, keeping one per team ────────────────
    # Use a CTE to find the single newsletter id to KEEP per team (MIN id),
    # then delete everything else.  Safe even if no duplicates exist.
    op.execute("""
        DELETE FROM newsletter_topics
        WHERE newsletter_id IN (
            SELECT tn.id
            FROM team_newsletters tn
            WHERE tn.id NOT IN (
                SELECT DISTINCT ON (team_id) id
                FROM team_newsletters
                ORDER BY team_id, created_at ASC NULLS LAST
            )
        )
    """)
    op.execute("""
        DELETE FROM team_newsletters
        WHERE id NOT IN (
            SELECT DISTINCT ON (team_id) id
            FROM team_newsletters
            ORDER BY team_id, created_at ASC NULLS LAST
        )
    """)

    # ── Enforce one-newsletter-per-team at the DB level ───────────────────
    op.create_unique_constraint(
        "uq_team_newsletters_team_id",
        "team_newsletters",
        ["team_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_team_newsletters_team_id",
        "team_newsletters",
        type_="unique",
    )
