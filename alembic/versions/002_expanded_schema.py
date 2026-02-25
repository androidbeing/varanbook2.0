"""002 – Expanded schema (Phase 2)

Adds:
  * New columns on tenants         (contact_person, contact_number, whatsapp_number, pin, upi_id, castes)
  * New columns on profiles        (time_of_birth, rashi, star, dhosam, qualification, profession,
                                    working_at, income_range, native_place, current_location,
                                    mobile, whatsapp, mother_occupation, siblings_details,
                                    privacy flags ×7)
  * New tables:
      - partner_preferences
      - shortlists
      - file_records
      - refresh_tokens
      - password_reset_tokens
      - audit_logs

Revision ID: 002
Revises:     001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── tenants – new columns ─────────────────────────────────────────────────
    op.add_column("tenants", sa.Column("contact_person", sa.String(200), nullable=True))
    op.add_column("tenants", sa.Column("contact_number", sa.String(20), nullable=True))
    op.add_column("tenants", sa.Column("whatsapp_number", sa.String(20), nullable=True))
    op.add_column("tenants", sa.Column("pin", sa.String(6), nullable=True))
    op.add_column("tenants", sa.Column("upi_id", sa.String(100), nullable=True))
    op.add_column(
        "tenants",
        sa.Column("castes", postgresql.ARRAY(sa.String()), nullable=True),
    )

    # ── profiles – new enum types ─────────────────────────────────────────────
    rashi_enum = postgresql.ENUM(
        "mesha", "vrishabha", "mithuna", "karkataka", "simha", "kanya",
        "thula", "vrishchika", "dhanus", "makara", "kumbha", "meena",
        name="rashi",
    )
    rashi_enum.create(op.get_bind(), checkfirst=True)

    star_enum = postgresql.ENUM(
        "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
        "punarvasu", "pushya", "ashlesha", "magha", "purva_phalguni",
        "uttara_phalguni", "hasta", "chitra", "swati", "vishakha",
        "anuradha", "jyeshtha", "mula", "purva_ashadha", "uttara_ashadha",
        "shravana", "dhanishtha", "shatabhisha", "purva_bhadrapada",
        "uttara_bhadrapada", "revati",
        name="star",
    )
    star_enum.create(op.get_bind(), checkfirst=True)

    dhosam_enum = postgresql.ENUM(
        "none", "chevvai", "rahu", "kethu", "shani", "multiple",
        name="dhosam",
    )
    dhosam_enum.create(op.get_bind(), checkfirst=True)

    qualification_enum = postgresql.ENUM(
        "below_10th", "sslc", "hsc", "diploma", "ug", "pg", "professional", "doctorate",
        name="qualification",
    )
    qualification_enum.create(op.get_bind(), checkfirst=True)

    income_range_enum = postgresql.ENUM(
        "below_2l", "2l_5l", "5l_10l", "10l_25l", "25l_50l", "above_50l",
        name="incomerange",
    )
    income_range_enum.create(op.get_bind(), checkfirst=True)

    # ── profiles – new columns ────────────────────────────────────────────────
    op.add_column("profiles", sa.Column("time_of_birth", sa.Time(), nullable=True))
    op.add_column("profiles", sa.Column("rashi", sa.Enum("mesha", "vrishabha", "mithuna", "karkataka", "simha", "kanya", "thula", "vrishchika", "dhanus", "makara", "kumbha", "meena", name="rashi", create_type=False), nullable=True))
    op.add_column("profiles", sa.Column("star", sa.Enum("ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra", "punarvasu", "pushya", "ashlesha", "magha", "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati", "vishakha", "anuradha", "jyeshtha", "mula", "purva_ashadha", "uttara_ashadha", "shravana", "dhanishtha", "shatabhisha", "purva_bhadrapada", "uttara_bhadrapada", "revati", name="star", create_type=False), nullable=True))
    op.add_column("profiles", sa.Column("dhosam", sa.Enum("none", "chevvai", "rahu", "kethu", "shani", "multiple", name="dhosam", create_type=False), nullable=True))
    op.add_column("profiles", sa.Column("qualification", sa.Enum("below_10th", "sslc", "hsc", "diploma", "ug", "pg", "professional", "doctorate", name="qualification", create_type=False), nullable=True))
    op.add_column("profiles", sa.Column("profession", sa.String(200), nullable=True))
    op.add_column("profiles", sa.Column("working_at", sa.String(200), nullable=True))
    op.add_column("profiles", sa.Column("income_range", sa.Enum("below_2l", "2l_5l", "5l_10l", "10l_25l", "25l_50l", "above_50l", name="incomerange", create_type=False), nullable=True))
    op.add_column("profiles", sa.Column("native_place", sa.String(100), nullable=True))
    op.add_column("profiles", sa.Column("current_location", sa.String(100), nullable=True))
    op.add_column("profiles", sa.Column("mobile", sa.String(20), nullable=True))
    op.add_column("profiles", sa.Column("whatsapp", sa.String(20), nullable=True))
    op.add_column("profiles", sa.Column("mother_occupation", sa.String(200), nullable=True))
    op.add_column("profiles", sa.Column("siblings_details", sa.Text(), nullable=True))
    # Privacy flags
    op.add_column("profiles", sa.Column("personal_visible", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("profiles", sa.Column("photo_visible", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("profiles", sa.Column("birth_visible", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("profiles", sa.Column("professional_visible", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("profiles", sa.Column("family_visible", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("profiles", sa.Column("contact_visible", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("profiles", sa.Column("horoscope_visible", sa.Boolean(), nullable=False, server_default="false"))

    # ── partner_preferences ───────────────────────────────────────────────────
    op.create_table(
        "partner_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("age_min", sa.Integer(), nullable=True),
        sa.Column("age_max", sa.Integer(), nullable=True),
        sa.Column("height_min_cm", sa.Integer(), nullable=True),
        sa.Column("height_max_cm", sa.Integer(), nullable=True),
        sa.Column("weight_min_kg", sa.Integer(), nullable=True),
        sa.Column("weight_max_kg", sa.Integer(), nullable=True),
        sa.Column("qualifications", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("income_ranges", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("marital_statuses", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("current_locations", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("native_locations", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("castes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("religions", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("dhosam", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("rashi", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("star", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ── shortlists ────────────────────────────────────────────────────────────
    # NOTE: SQLAlchemy auto-creates the shortliststatus enum via op.create_table()

    op.create_table(
        "shortlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("from_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Enum("shortlisted", "accepted", "rejected", name="shortliststatus"), nullable=False, server_default="shortlisted"),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("from_profile_id", "to_profile_id", name="uq_shortlist_pair"),
    )

    # ── file_records ──────────────────────────────────────────────────────────
    # NOTE: SQLAlchemy auto-creates the scanstatus enum via op.create_table()

    op.create_table(
        "file_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("object_key", sa.String(1024), nullable=False, unique=True),
        sa.Column("original_filename", sa.String(512), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("purpose", sa.String(50), nullable=True),
        sa.Column("scan_status", sa.Enum("pending", "clean", "infected", "error", name="scanstatus"), nullable=False, server_default="pending"),
        sa.Column("scan_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── refresh_tokens ────────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("device_info", sa.String(512), nullable=True),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── password_reset_tokens ─────────────────────────────────────────────────
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── audit_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    op.create_index("ix_shortlists_from_profile", "shortlists", ["from_profile_id"])
    op.create_index("ix_shortlists_to_profile", "shortlists", ["to_profile_id"])
    op.create_index("ix_file_records_profile", "file_records", ["profile_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("password_reset_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("file_records")
    op.drop_index("ix_shortlists_to_profile", table_name="shortlists")
    op.drop_index("ix_shortlists_from_profile", table_name="shortlists")
    op.drop_table("shortlists")
    op.drop_table("partner_preferences")

    # Drop privacy flags
    for col in ("horoscope_visible", "contact_visible", "family_visible",
                "professional_visible", "birth_visible", "photo_visible", "personal_visible"):
        op.drop_column("profiles", col)

    # Drop profile columns
    for col in ("siblings_details", "mother_occupation", "whatsapp", "mobile",
                "current_location", "native_place", "income_range", "working_at",
                "profession", "qualification", "dhosam", "star", "rashi", "time_of_birth"):
        op.drop_column("profiles", col)

    # Drop tenant columns
    for col in ("castes", "upi_id", "pin", "whatsapp_number", "contact_number", "contact_person"):
        op.drop_column("tenants", col)

    # Drop enum types
    for name in ("incomerange", "qualification", "dhosam", "star", "rashi",
                 "shortliststatus", "scanstatus"):
        op.execute(f"DROP TYPE IF EXISTS {name}")
