"""012 – Add self_registration_enabled to tenants

Allows tenant admins to enable a public self-registration link
(/join/<slug>) so members can register themselves.

Revision ID: 012
Revises:     815bd765c837
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "815bd765c837"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "self_registration_enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
            comment="When True, members can self-register via /join/<slug>",
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "self_registration_enabled")
