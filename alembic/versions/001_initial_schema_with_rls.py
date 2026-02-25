"""
001_initial_schema_with_rls.py

Alembic migration: initial schema with Row-Level Security (RLS).

What this migration creates:
  1. tables: tenants, users, profiles (with all columns)
  2. indexes for performance
  3. Postgres RLS policies on users and profiles tables
     - Policy uses   current_setting('app.current_tenant_id')::uuid
     - Application sets this via: SET LOCAL app.current_tenant_id = '<uuid>'
  4. A restricted DB role 'app_user' that cannot bypass RLS.
  5. SUPER_ADMIN bypass: handled by connecting as a different DB role
     with BYPASSRLS attribute (configured outside the app).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Extensions ─────────────────────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')  # gen_random_uuid()

    # ── 2. Enum types ──────────────────────────────────────────────────────────
    # NOTE: enum types (userrole, maritalstatus, gender, profilestatus) are
    # auto-created by SQLAlchemy when op.create_table() processes the Enum columns.
    # Do NOT create them manually here or they will be created twice.

    # ── 3. Tenants table (NOT RLS-protected; super-admin only) ─────────────────
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(320), nullable=False),
        sa.Column("contact_phone", sa.String(20), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("plan", sa.String(50), nullable=False, server_default="starter"),
        sa.Column("max_users", sa.Integer, nullable=False, server_default="500"),
        sa.Column("max_admins", sa.Integer, nullable=False, server_default="5"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])

    # ── 4. Users table ─────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(1024), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("role", sa.Enum("super_admin", "admin", "member",
                                  name="userrole"), nullable=False,
                  server_default="member"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fcm_token", sa.String(512), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_email", "users", ["email"])

    # ── 5. Profiles table ──────────────────────────────────────────────────────
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gender", sa.Enum("male", "female", "other", name="gender"),
                  nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=False),
        sa.Column("height_cm", sa.Float, nullable=True),
        sa.Column("weight_kg", sa.Float, nullable=True),
        sa.Column("complexion", sa.String(50), nullable=True),
        sa.Column("blood_group", sa.String(10), nullable=True),
        sa.Column("marital_status",
                  sa.Enum("never_married", "divorced", "widowed", "awaiting_divorce",
                          name="maritalstatus"),
                  nullable=False, server_default="never_married"),
        sa.Column("disabilities", sa.Text, nullable=True),
        sa.Column("religion", sa.String(100), nullable=True),
        sa.Column("caste", sa.String(100), nullable=True),
        sa.Column("sub_caste", sa.String(100), nullable=True),
        sa.Column("gotra", sa.String(100), nullable=True),
        sa.Column("mother_tongue", sa.String(100), nullable=True),
        sa.Column("birth_time", sa.String(20), nullable=True),
        sa.Column("birth_place", sa.String(200), nullable=True),
        sa.Column("nakshatra", sa.String(100), nullable=True),
        sa.Column("manglik", sa.Boolean, nullable=True),
        sa.Column("education", sa.String(200), nullable=True),
        sa.Column("occupation", sa.String(200), nullable=True),
        sa.Column("annual_income_inr", sa.Integer, nullable=True),
        sa.Column("employer", sa.String(200), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=False, server_default="India"),
        sa.Column("father_name", sa.String(200), nullable=True),
        sa.Column("father_occupation", sa.String(200), nullable=True),
        sa.Column("mother_name", sa.String(200), nullable=True),
        sa.Column("siblings", sa.Integer, nullable=True),
        sa.Column("photo_keys", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("horoscope_key", sa.String(512), nullable=True),
        sa.Column("status",
                  sa.Enum("draft", "active", "suspended", "matched",
                          name="profilestatus"),
                  nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_profiles_tenant_id", "profiles", ["tenant_id"])
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"])

    # ── 6. Row-Level Security ──────────────────────────────────────────────────
    # Enable RLS on tenant-scoped tables
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY")  # even table owner is restricted

    op.execute("ALTER TABLE profiles ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE profiles FORCE ROW LEVEL SECURITY")

    # Create the application DB role (read/write, no BYPASSRLS)
    op.execute("""
        DO $$ BEGIN
            CREATE ROLE app_user NOINHERIT LOGIN PASSWORD 'changeme_in_production';
        EXCEPTION WHEN duplicate_object THEN null;
        END $$
    """)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user")

    # RLS policy for users table
    # Reads: only rows matching current tenant
    # Super-admins (connecting as postgres role) bypass via BYPASSRLS attribute
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON users
        AS PERMISSIVE
        FOR ALL
        TO app_user
        USING (
            tenant_id IS NULL  -- SUPER_ADMINs have NULL tenant_id; allow them through
            OR tenant_id = current_setting('app.current_tenant_id', true)::uuid
        )
        WITH CHECK (
            tenant_id IS NULL
            OR tenant_id = current_setting('app.current_tenant_id', true)::uuid
        )
    """)

    # RLS policy for profiles table
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON profiles
        AS PERMISSIVE
        FOR ALL
        TO app_user
        USING (
            tenant_id = current_setting('app.current_tenant_id', true)::uuid
        )
        WITH CHECK (
            tenant_id = current_setting('app.current_tenant_id', true)::uuid
        )
    """)

    # ── 7. updated_at auto-update trigger ─────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    for table in ("tenants", "users", "profiles"):
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop triggers
    for table in ("tenants", "users", "profiles"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON profiles")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON users")

    # Disable RLS
    op.execute("ALTER TABLE profiles DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")

    # Drop tables
    op.drop_table("profiles")
    op.drop_table("users")
    op.drop_table("tenants")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS profilestatus")
    op.execute("DROP TYPE IF EXISTS gender")
    op.execute("DROP TYPE IF EXISTS maritalstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
