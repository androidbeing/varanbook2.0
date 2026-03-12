"""009 – Enforce one active subscription per member per tenant

Adds a partial unique index on member_subscriptions so that at most one row
with status='active' can exist for a given (user_id, tenant_id) pair.

This complements the application-level 409 check in create_subscription and
protects against duplicate writes that could arrive in a race condition.

Revision ID: 009
Revises:     008
Create Date: 2026-03-12
"""

from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX uq_one_active_sub_per_member
        ON member_subscriptions (user_id, tenant_id)
        WHERE status = 'active'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_one_active_sub_per_member")
