"""
models/user.py – User ORM model (tenant-scoped, RLS-protected).

A User can be:
  - SUPER_ADMIN  : platform operator (no tenant)
  - ADMIN        : matrimonial centre admin
  - MEMBER       : registered candidate
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MEMBER = "member"


class User(Base):
    """
    Tenant-scoped user table.

    RLS policy (created in migration):
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)

    SUPER_ADMINs bypass RLS because they use the postgres superuser role
    or a dedicated role with BYPASSRLS.
    """

    __tablename__ = "users"

    # ── PK ───────────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Tenant FK ─────────────────────────────────────────────────────────────
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,          # NULL for SUPER_ADMINs
        index=True,
    )

    # ── Credentials ──────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)

    # ── Identity ─────────────────────────────────────────────────────────────
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── Role / status ─────────────────────────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x], create_type=False),
        nullable=False,
        default=UserRole.MEMBER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Device / push ─────────────────────────────────────────────────────────
    fcm_token: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # ── Audit ─────────────────────────────────────────────────────────────────
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    tenant: Mapped["Tenant"] = relationship(  # noqa: F821
        "Tenant", back_populates="users"
    )
    profile: Mapped["Profile"] = relationship(  # noqa: F821
        "Profile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User email={self.email} role={self.role}>"
