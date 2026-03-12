"""
models/membership_plan.py – Membership plan ORM models.

Three tiers:
  Silver   (3 months)  – Start your search
  Gold     (6 months)  – Grow your connections
  Platinum (12 months) – Your complete journey

Architecture:
  - MembershipPlanTemplate : platform-level plan definitions (SuperAdmin-managed)
  - TenantPlanOverride     : per-tenant price overrides (if tenant has permission)
  - MemberSubscription     : actual subscription assigned to a member by an admin
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class MembershipPlanTemplate(Base):
    """
    Platform-level plan template – managed exclusively by SuperAdmin.

    duration_months is immutable after creation (3, 6, or 12 months).
    base_price_inr is the default price used unless a tenant has an override.
    """

    __tablename__ = "membership_plan_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True,
        comment="Display name e.g. Silver, Gold, Platinum",
    )
    tagline: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_months: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Fixed duration in months: 3, 6, or 12 — immutable after creation",
    )
    base_price_inr: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False,
        comment="Default price in INR; tenants may override this if granted permission",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    features: Mapped[list | None] = mapped_column(
        JSONB, nullable=True,
        comment="JSON array of feature strings e.g. ['Unlimited shortlists', 'Email alerts']",
    )
    max_interests: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Max interest requests a member may send per subscription period; NULL = unlimited",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="Display order (ascending); Silver=1, Gold=2, Platinum=3",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    tenant_overrides: Mapped[list["TenantPlanOverride"]] = relationship(
        "TenantPlanOverride", back_populates="plan_template", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["MemberSubscription"]] = relationship(
        "MemberSubscription", back_populates="plan_template"
    )

    def __repr__(self) -> str:
        return f"<MembershipPlanTemplate name={self.name} months={self.duration_months}>"


class TenantPlanOverride(Base):
    """
    Per-tenant price override for a plan template.

    Only exists when:
      1. The tenant has `can_override_plan_prices = True` (set by SuperAdmin), AND
      2. The tenant admin has explicitly set a custom price.

    NULL custom_price_inr means "use the template's base_price_inr".
    """

    __tablename__ = "tenant_plan_overrides"
    __table_args__ = (
        UniqueConstraint("tenant_id", "plan_template_id", name="uq_tenant_plan_override"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("membership_plan_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    custom_price_inr: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True,
        comment="NULL → use template base price; otherwise this is the tenant-specific price",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    plan_template: Mapped["MembershipPlanTemplate"] = relationship(
        "MembershipPlanTemplate", back_populates="tenant_overrides"
    )

    def __repr__(self) -> str:
        return f"<TenantPlanOverride tenant={self.tenant_id} plan={self.plan_template_id}>"


class MemberSubscription(Base):
    """
    A membership subscription assigned to a member by a tenant admin.

    price_paid_inr is a historical snapshot of the price at the time of
    assignment, so billing history remains accurate even if template prices
    change later.
    """

    __tablename__ = "member_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("membership_plan_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    price_paid_inr: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False,
        comment="Price snapshot at time of assignment for billing history accuracy",
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="Subscription start date (UTC)",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="Subscription expiry date = starts_at + duration_months",
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status", values_callable=lambda x: [e.value for e in x]),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    expiry_warning_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="True once the 3-day expiry warning email has been dispatched",
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Admin user who assigned this subscription",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    plan_template: Mapped["MembershipPlanTemplate"] = relationship(
        "MembershipPlanTemplate", back_populates="subscriptions"
    )

    def __repr__(self) -> str:
        return (
            f"<MemberSubscription user={self.user_id} "
            f"plan={self.plan_template_id} status={self.status}>"
        )
