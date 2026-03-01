"""Make profile gender and date_of_birth nullable.

Members onboard section-by-section; requiring gender+DOB on first save
blocked the Personal Details section from being saved independently.

Revision ID: 004
Revises:     003
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "profiles",
        "gender",
        existing_type=sa.Enum(
            "male", "female", "other",
            name="gender",
            create_type=False,
        ),
        nullable=True,
    )
    op.alter_column(
        "profiles",
        "date_of_birth",
        existing_type=sa.Date(),
        nullable=True,
    )


def downgrade() -> None:
    # Backfill NULLs with placeholders before restoring NOT NULL constraint
    op.execute("UPDATE profiles SET date_of_birth = '1990-01-01' WHERE date_of_birth IS NULL")
    op.execute("UPDATE profiles SET gender = 'other' WHERE gender IS NULL")
    op.alter_column(
        "profiles",
        "date_of_birth",
        existing_type=sa.Date(),
        nullable=False,
    )
    op.alter_column(
        "profiles",
        "gender",
        existing_type=sa.Enum(
            "male", "female", "other",
            name="gender",
            create_type=False,
        ),
        nullable=False,
    )
