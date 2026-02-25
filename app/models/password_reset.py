"""
models/password_reset.py – One-time password reset token.

Flow:
  1. POST /auth/forgot-password  → generate token, store hash, email link.
  2. POST /auth/reset-password   → verify token, set new password, mark used.

The raw token is a URL-safe random string (secrets.token_urlsafe(32)).
Only the hash is persisted; the user receives the raw token in their email.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PasswordResetToken(Base):
    """One-time password reset token row."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # SHA-256 hex digest of the raw token (fast; not a password – no bcrypt needed)
    token_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True,
        comment="SHA-256 hex of raw URL-safe token",
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User")  # noqa: F821
