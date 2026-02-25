"""
models/audit_log.py – Immutable audit trail for all mutating actions.

Written by AuditMiddleware and specific router helpers.
Intentionally NOT protected by RLS so super-admins can query cross-tenant.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditLog(Base):
    """Append-only audit log row."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Tenant context (null for super-admin actions that have no tenant scope)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    # Acting user (null for unauthenticated events like failed logins)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Action identifier: e.g. "user.login", "profile.update", "shortlist.create"
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Resource being acted upon
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Optional before/after snapshot or summarised request body
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # HTTP outcome (200, 201, 400, 403, 500, …)
    status_code: Mapped[int | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
