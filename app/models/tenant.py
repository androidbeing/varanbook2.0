"""
models/tenant.py – Tenant ORM model.

A Tenant represents one matrimonial centre (client organisation).
It owns its own set of users and profiles isolated via RLS.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tenant(Base):
    """
    Master tenant registry (not RLS-protected itself – lives in public schema
    and is only writable by the platform super-admin role).
    """

    __tablename__ = "tenants"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Globally unique tenant identifier",
    )

    # ── Identity ─────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Human-readable centre name"
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="URL-safe identifier used in subdomain / header",
    )
    domain: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Custom domain if white-labelled"
    )

    # ── Contact (all required by spec) ────────────────────────────────────────
    contact_person: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Primary contact person name"
    )
    contact_email: Mapped[str] = mapped_column(String(320), nullable=False)
    # E.164 validated at schema layer: +91XXXXXXXXXX
    contact_number: Mapped[str] = mapped_column(String(20), nullable=False)
    whatsapp_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 6-digit numeric postal PIN
    pin: Mapped[str | None] = mapped_column(String(6), nullable=True)
    # UPI ID e.g. vivahkendra@upi  – pattern validated at schema layer
    upi_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Communities/castes this centre serves
    castes: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True,
        comment="Caste communities served by this centre",
    )

    # ── Plan / billing ────────────────────────────────────────────────────────
    plan: Mapped[str] = mapped_column(
        String(50),
        default="starter",
        comment="starter | growth | enterprise",
    )
    max_users: Mapped[int] = mapped_column(default=500)
    max_admins: Mapped[int] = mapped_column(default=5)

    # ── Status ────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Audit ─────────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    users: Mapped[list["User"]] = relationship(  # noqa: F821
        "User", back_populates="tenant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tenant slug={self.slug} plan={self.plan}>"
