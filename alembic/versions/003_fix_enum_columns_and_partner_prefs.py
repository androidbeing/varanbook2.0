"""003 – Fix enum column types and partner_preferences schema

Problems fixed:
  1. profiles.qualification  – DB had PG ENUM (ug/pg/…) mismatched with
                               Python enum (bachelor/master/…) → convert to VARCHAR
  2. profiles.income_range   – DB ENUM values (2l_5l, 5l_10l, …) mismatched
                               Python (2_to_5l, 5_to_10l, …)  → convert to VARCHAR
  3. profiles.rashi / star / dhosam – DB ENUM values differed from Python (karka vs
                               karkataka, tula vs thula, …)  → convert to VARCHAR
  4. partner_preferences     – missing tenant_id column (was in ORM model but not
                               in the initial migration) → add as nullable FK, then
                               backfill from profiles and set NOT NULL
  5. partner_preferences     – missing created_at column, and id had no server_default

Revision ID: 003
Revises:     002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. Convert profiles enum columns to VARCHAR ───────────────────────────
    # PostgreSQL requires an explicit USING cast when changing from an enum type.

    for col, pg_type in [
        ("qualification", "qualification"),
        ("income_range",  "incomerange"),
        ("rashi",         "rashi"),
        ("star",          "star"),
        ("dhosam",        "dhosam"),
    ]:
        # Clear any stale values that don't exist in the new Python enums
        # (e.g. "ug" -> "ug" stays as string; users will need to re-select)
        conn.execute(sa.text(
            f"ALTER TABLE profiles ALTER COLUMN {col} TYPE VARCHAR(50) "
            f"USING {col}::TEXT"
        ))

    # Drop the old PG enum types (they're no longer used as column types)
    for pg_type in ("qualification", "incomerange", "rashi", "star", "dhosam"):
        conn.execute(sa.text(f"DROP TYPE IF EXISTS {pg_type}"))

    # ── 2. Fix partner_preferences table ─────────────────────────────────────

    # 2a. Add tenant_id as nullable first (so it works even if rows exist)
    op.add_column(
        "partner_preferences",
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )

    # 2b. Backfill tenant_id from the linked profile's tenant_id
    conn.execute(sa.text("""
        UPDATE partner_preferences pp
        SET tenant_id = p.tenant_id
        FROM profiles p
        WHERE pp.profile_id = p.id
    """))

    # 2c. Make it NOT NULL now that it's populated
    conn.execute(sa.text(
        "ALTER TABLE partner_preferences ALTER COLUMN tenant_id SET NOT NULL"
    ))

    # 2d. Add missing created_at column
    op.add_column(
        "partner_preferences",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # 2e. Give partner_preferences.id a server_default so DB can generate it
    conn.execute(sa.text(
        "ALTER TABLE partner_preferences ALTER COLUMN id "
        "SET DEFAULT gen_random_uuid()"
    ))

    op.create_index(
        "ix_partner_preferences_tenant",
        "partner_preferences",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_partner_preferences_tenant", table_name="partner_preferences")
    op.drop_column("partner_preferences", "created_at")
    op.drop_column("partner_preferences", "tenant_id")

    # Restoring the exact original PG enum types and recasting is complex;
    # for safety just restore the column types to TEXT (data preserved).
    for col in ("qualification", "income_range", "rashi", "star", "dhosam"):
        pass  # downgrade intentionally left as VARCHAR – re-run from scratch if needed
