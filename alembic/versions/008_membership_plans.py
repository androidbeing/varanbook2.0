"""008 – Membership Plans

Adds the membership plan subsystem:

  * CREATE TABLE membership_plan_templates
  * CREATE TABLE tenant_plan_overrides
  * CREATE TABLE member_subscriptions  (with subscription_status enum)
  * ALTER TABLE tenants ADD COLUMN can_override_plan_prices

Seeds the three default platform plan templates:
  - Silver   (3 months)  ₹599
  - Gold     (6 months)  ₹999
  - Platinum (12 months) ₹1699

Revision ID: 008
Revises:     007
Create Date: 2026-03-11
"""

import uuid as _uuid
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None

# Stable UUIDs for seeded plan templates (deterministic for cross-env consistency)
_SILVER_ID = str(_uuid.UUID("00000000-0000-0000-0000-000000000001"))
_GOLD_ID = str(_uuid.UUID("00000000-0000-0000-0000-000000000002"))
_PLATINUM_ID = str(_uuid.UUID("00000000-0000-0000-0000-000000000003"))


def upgrade() -> None:
    # ── 1. membership_plan_templates ─────────────────────────────────────────
    op.create_table(
        "membership_plan_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("tagline", sa.Text, nullable=True),
        sa.Column("duration_months", sa.Integer, nullable=False),
        sa.Column("base_price_inr", sa.Numeric(10, 2), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("features", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── 2. tenant_plan_overrides ─────────────────────────────────────────────
    op.create_table(
        "tenant_plan_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "plan_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("membership_plan_templates.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("custom_price_inr", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("tenant_id", "plan_template_id", name="uq_tenant_plan_override"),
    )

    # ── 3. subscription_status enum + member_subscriptions ──────────────────
    # asyncpg doesn't support DO $$ blocks reliably in migration scripts;
    # check pg_type directly and only CREATE if the type is absent.
    conn = op.get_bind()
    row = conn.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'subscription_status'")
    ).scalar()
    if not row:
        conn.execute(
            sa.text(
                "CREATE TYPE subscription_status AS ENUM ('active', 'expired', 'cancelled')"
            )
        )

    op.create_table(
        "member_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "plan_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("membership_plan_templates.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("price_paid_inr", sa.Numeric(10, 2), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active", "expired", "cancelled",
                name="subscription_status",
                create_type=False,   # type was created (or verified) above
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── 4. tenants – new column ──────────────────────────────────────────────
    op.add_column(
        "tenants",
        sa.Column(
            "can_override_plan_prices",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
            comment="Grants tenant admin the ability to set custom membership plan prices",
        ),
    )

    # ── 5. Seed default plan templates ───────────────────────────────────────
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC for pg
    plan_templates_table = sa.table(
        "membership_plan_templates",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.Text),
        sa.column("tagline", sa.Text),
        sa.column("duration_months", sa.Integer),
        sa.column("base_price_inr", sa.Numeric(10, 2)),
        sa.column("description", sa.Text),
        sa.column("features", postgresql.JSONB),
        sa.column("max_interests", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    op.bulk_insert(
        plan_templates_table,
        [
            {
                "id": _SILVER_ID,
                "name": "Silver",
                "tagline": "Start your search",
                "duration_months": 3,
                "base_price_inr": 599.00,
                "description": (
                    "A 3-month starter membership to explore profiles and "
                    "make your first connections."
                ),
                "features": [
                    "Browse unlimited profiles",
                    "Send up to 10 interest requests",
                    "Email match alerts",
                    "Basic profile visibility",
                ],
                "max_interests": 10,
                "is_active": True,
                "sort_order": 1,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": _GOLD_ID,
                "name": "Gold",
                "tagline": "Grow your connections",
                "duration_months": 6,
                "base_price_inr": 999.00,
                "description": (
                    "A 6-month membership for dedicated search with enhanced "
                    "visibility and more connection opportunities."
                ),
                "features": [
                    "Browse unlimited profiles",
                    "Send up to 30 interest requests",
                    "Priority email & WhatsApp alerts",
                    "Enhanced profile badge",
                    "Horoscope matching access",
                ],
                "max_interests": 30,
                "is_active": True,
                "sort_order": 2,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": _PLATINUM_ID,
                "name": "Platinum",
                "tagline": "Your complete journey",
                "duration_months": 12,
                "base_price_inr": 1699.00,
                "description": (
                    "Our premium 1-year membership for the complete matrimonial "
                    "journey with all features unlocked."
                ),
                "features": [
                    "Browse unlimited profiles",
                    "Unlimited interest requests",
                    "Priority support",
                    "Premium profile badge",
                    "Horoscope matching access",
                    "Contact details access",
                    "Dedicated relationship manager",
                ],
                "max_interests": None,
                "is_active": True,
                "sort_order": 3,
                "created_at": now,
                "updated_at": now,
            },
        ],
    )


def downgrade() -> None:
    op.drop_column("tenants", "can_override_plan_prices")
    op.drop_table("member_subscriptions")
    op.drop_table("tenant_plan_overrides")
    op.drop_table("membership_plan_templates")
    op.execute("DROP TYPE IF EXISTS subscription_status")
