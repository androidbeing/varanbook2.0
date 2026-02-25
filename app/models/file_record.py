"""
models/file_record.py – Persistent metadata for every uploaded file.

S3 object keys are also stored on the Profile row for quick access,
but file_records provides a full audit trail including:
  - MIME type and size
  - Virus scan status
  - Upload timestamp and uploader
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScanStatus(str, enum.Enum):
    PENDING = "pending"     # scan not yet run
    CLEAN = "clean"         # passed AV scan
    INFECTED = "infected"   # virus detected; file quarantined
    ERROR = "error"         # scan service error


class FileRecord(Base):
    """
    One row per uploaded file.

    Supports:
      - Per-tenant S3 prefix: tenant-{tenant_id}/profiles/{profile_id}/photos/
      - Virus scan state machine
      - Link back to the owning profile and uploader
    """

    __tablename__ = "file_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── S3 metadata ───────────────────────────────────────────────────────────
    object_key: Mapped[str] = mapped_column(
        String(1024), nullable=False, unique=True,
        comment="Full S3 object key including prefix",
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # File size in bytes; BigInteger supports up to ~9 EB
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    purpose: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="profile_photo | horoscope",
    )

    # ── Virus scan ────────────────────────────────────────────────────────────
    scan_status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus, values_callable=lambda x: [e.value for e in x], create_type=False), nullable=False, default=ScanStatus.PENDING
    )
    scan_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
