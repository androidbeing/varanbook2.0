"""
models/shortlist.py – Shortlist / Accept ORM model.

Tracks profile-to-profile interest expressions.
States: shortlisted → accepted | rejected
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ShortlistStatus(str, enum.Enum):
    SHORTLISTED = "shortlisted"   # sender expressed interest
    ACCEPTED = "accepted"          # recipient accepted
    REJECTED = "rejected"          # recipient declined


class Shortlist(Base):
    """
    Directed interest graph between profiles.

    from_profile_id → to_profile_id with a status:
      shortlisted  : initial interest shown
      accepted     : mutual confirmation
      rejected     : politely declined

    RLS: both from_ and to_ profiles must be in the same tenant
    (enforced by tenant_id column shared with other tenant-scoped tables).
    """

    __tablename__ = "shortlists"
    __table_args__ = (
        UniqueConstraint(
            "from_profile_id", "to_profile_id",
            name="uq_shortlist_pair",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Tenant copied for RLS
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ShortlistStatus] = mapped_column(
        Enum(ShortlistStatus, values_callable=lambda x: [e.value for e in x], create_type=False), nullable=False, default=ShortlistStatus.SHORTLISTED
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    from_profile: Mapped["Profile"] = relationship(  # noqa: F821
        "Profile", foreign_keys=[from_profile_id], back_populates="shortlists_sent"
    )
    to_profile: Mapped["Profile"] = relationship(  # noqa: F821
        "Profile", foreign_keys=[to_profile_id], back_populates="shortlists_received"
    )
