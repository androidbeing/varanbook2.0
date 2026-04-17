"""014 – Make users.email nullable and add partial unique index on users.phone

Allows phone-only member registration:
  - users.email becomes nullable (phone-only members may not supply an email).
  - A partial unique index on users.phone (WHERE phone IS NOT NULL) prevents two
    users from sharing the same phone number while still allowing multiple
    email-only users who have no phone at all.

This is a merge migration that combines the two current heads (013 and
815bd765c837) into a single linear chain going forward.

Revision ID: 014
Revises:     013, 815bd765c837
Merge:       merge two current heads
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "014"
down_revision = ("013", "815bd765c837")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Allow phone-only registrations – email is no longer mandatory.
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(320),
        nullable=True,
    )

    # 2. Partial unique index: two users cannot share the same phone number,
    #    but multiple users without a phone (NULL) are allowed.
    #    NULLS NOT DISTINCT is PostgreSQL 15+; use a WHERE clause for compat.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_users_phone
        ON users (phone)
        WHERE phone IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_users_phone")

    # WARNING: any phone-only rows (email IS NULL) must be removed or patched
    # before this succeeds in production.
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(320),
        nullable=False,
    )
