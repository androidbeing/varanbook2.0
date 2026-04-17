"""013 – Add phone_verified_at to users

Records the timestamp when a user's phone number was verified via OTP
(Firebase Phone Auth). NULL means phone has not been verified yet.

Revision ID: 013
Revises:     012
Create Date: 2026-04-11
"""

from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "phone_verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp when the user's phone was verified via OTP",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "phone_verified_at")
