"""007 – Ensure horoscope columns exist on profiles table.

Safety migration: adds horoscope_key and horoscope_visible using
"IF NOT EXISTS" so it is safe to run even if the columns were already
created by an earlier migration or manual DDL.

Revision ID: 007
Revises:     006
Create Date: 2026-03-07
"""

from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Ensure horoscope_key exists (was in 001 but may be missing on older DBs)
    conn.execute(sa.text("""
        ALTER TABLE profiles
        ADD COLUMN IF NOT EXISTS horoscope_key VARCHAR(512) NULL
    """))

    # Ensure horoscope_visible exists (was in 002 but may be missing on older DBs)
    conn.execute(sa.text("""
        ALTER TABLE profiles
        ADD COLUMN IF NOT EXISTS horoscope_visible BOOLEAN NOT NULL DEFAULT FALSE
    """))


def downgrade() -> None:
    # These columns are part of the core schema; dropping is destructive.
    # No-op downgrade: the columns are left in place.
    pass
