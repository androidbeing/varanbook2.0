"""
models/partner_preference.py – Partner preference ORM model.

Stores what a candidate is looking for in a match.
Currently one-to-one with Profile.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PartnerPreference(Base):
    """
    Partner search preferences – each field is optional (nullable).

    Arrays (rashi, star, dhosam, qualification, income_range,
    current_locations, native_locations) allow multiple acceptable values.
    """

    __tablename__ = "partner_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    # Denormalised for RLS
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Age range ─────────────────────────────────────────────────────────────
    age_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Height (cm) ───────────────────────────────────────────────────────────
    height_min_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_max_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Weight (kg) ───────────────────────────────────────────────────────────
    weight_min_kg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_max_kg: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Multi-value preference fields (Postgres text arrays) ──────────────────
    # acceptable qualification levels
    qualifications: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    # acceptable income ranges
    income_ranges: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    # preferred current city/location strings
    current_locations: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    # preferred native place strings
    native_locations: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    # acceptable dhosam values (from Dhosam enum)
    dhosam: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    # acceptable rashi values
    rashi: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    # acceptable star/nakshatra values
    star: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    # acceptable castes
    castes: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    # acceptable religions
    religions: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # ── Marital status ────────────────────────────────────────────────────────
    marital_statuses: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )

    # ── Audit ─────────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    profile: Mapped["Profile"] = relationship(  # noqa: F821
        "Profile", back_populates="partner_preference"
    )
