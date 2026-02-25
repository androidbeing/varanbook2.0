"""
models/refresh_token.py – Hashed refresh token store.

Refresh tokens are stored as bcrypt hashes so that even if the `refresh_tokens`
table is compromised, the raw tokens cannot be replayed.

Lifecycle:
  1. Login / first token request → create row.
  2. /auth/refresh → verify hash, rotate (invalidate old, create new).
  3. /auth/logout  → mark revoked.
  4. A nightly cleanup job prunes expired rows.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RefreshToken(Base):
    """
    Persisted hashed refresh token.

    token_hash  : bcrypt hash of the raw refresh token JWT string
    device_info : optional User-Agent / device fingerprint for UX display
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The bcrypt hash; never store the raw JWT
    token_hash: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)

    # Optional device context (User-Agent truncated to 512 chars)
    device_info: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Soft-delete instead of hard-delete so logout is immediate
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationship ──────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User")  # noqa: F821
