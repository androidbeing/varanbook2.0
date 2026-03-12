"""010 – Add max_interests to membership_plan_templates

Adds `max_interests` (Integer, nullable) to membership_plan_templates.
NULL means unlimited (Platinum).  Back-fills the three seeded plans:
  Silver   → 10
  Gold     → 30
  Platinum → NULL  (unlimited)

Revision ID: 010
Revises:     009
Create Date: 2026-03-12
"""

from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None

_SILVER_ID = "00000000-0000-0000-0000-000000000001"
_GOLD_ID = "00000000-0000-0000-0000-000000000002"


def upgrade() -> None:
    op.add_column(
        "membership_plan_templates",
        sa.Column(
            "max_interests",
            sa.Integer,
            nullable=True,
            comment="Max interest requests per subscription period; NULL = unlimited",
        ),
    )
    # Back-fill the three seeded plans
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE membership_plan_templates SET max_interests = 10  WHERE id = :id"
        ),
        {"id": _SILVER_ID},
    )
    conn.execute(
        sa.text(
            "UPDATE membership_plan_templates SET max_interests = 30  WHERE id = :id"
        ),
        {"id": _GOLD_ID},
    )
    # Platinum stays NULL (already NULL by default)


def downgrade() -> None:
    op.drop_column("membership_plan_templates", "max_interests")
