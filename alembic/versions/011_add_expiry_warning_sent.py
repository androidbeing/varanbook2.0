"""011 – Add expiry_warning_sent to member_subscriptions

Tracks whether the 3-day expiry warning email has been sent for a
subscription so the daily background sweep doesn't re-send it.

Revision ID: 011
Revises:     010
Create Date: 2026-03-12
"""

from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "member_subscriptions",
        sa.Column(
            "expiry_warning_sent",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
            comment="True once the 3-day expiry warning email has been dispatched",
        ),
    )


def downgrade() -> None:
    op.drop_column("member_subscriptions", "expiry_warning_sent")
