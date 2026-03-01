"""Auto-promote draft profiles to active and change default to active.

Problem:
  New profiles created by members through the UI default to 'draft' status.
  The Browse Profiles endpoint only shows 'active' profiles to members, so
  members can't see each other even after filling their biodata.

Fix:
  1. Promote all existing 'draft' profiles to 'active'.
  2. Change the server_default for the status column from 'draft' to 'active'
     so new profiles start as visible immediately.

Revision ID: 005
Revises:     004
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Promote all existing draft profiles to active
    op.execute("UPDATE profiles SET status = 'active' WHERE status = 'draft'")

    # 2. Change the column default so future INSERT without explicit status = 'active'
    op.alter_column(
        "profiles",
        "status",
        existing_type=sa.Enum(
            "draft", "active", "suspended", "matched",
            name="profilestatus",
            create_type=False,
        ),
        server_default="active",
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "profiles",
        "status",
        existing_type=sa.Enum(
            "draft", "active", "suspended", "matched",
            name="profilestatus",
            create_type=False,
        ),
        server_default="draft",
        nullable=False,
    )
