"""
schemas/membership_plan.py – Pydantic request/response schemas for
membership plans, tenant price overrides, and member subscriptions.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field

# Reusable annotated type for INR prices stored to 2 decimal places
PriceINR = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]


# ── Plan Template (SuperAdmin-managed) ────────────────────────────────────────

class PlanTemplateCreate(BaseModel):
    """Payload for POST /admin/plan-templates (SuperAdmin only)."""

    name: str = Field(..., min_length=1, max_length=100, examples=["Silver"])
    tagline: str | None = Field(None, max_length=200, examples=["Start your search"])
    duration_months: Literal[3, 6, 12] = Field(
        ..., description="Fixed plan duration in months – immutable after creation"
    )
    base_price_inr: PriceINR = Field(..., examples=[599.00])
    description: str | None = Field(None, max_length=1000)
    features: list[str] = Field(
        default_factory=list,
        examples=[["Unlimited browsing", "10 interest requests"]],
    )
    is_active: bool = True
    sort_order: int = Field(0, ge=0)


class PlanTemplateUpdate(BaseModel):
    """Payload for PATCH /admin/plan-templates/{id}.

    duration_months is intentionally excluded – it is immutable after creation.
    """

    name: str | None = Field(None, min_length=1, max_length=100)
    tagline: str | None = None
    base_price_inr: PriceINR | None = None
    description: str | None = None
    features: list[str] | None = None
    is_active: bool | None = None
    sort_order: int | None = Field(None, ge=0)


class PlanTemplateRead(BaseModel):
    """Full plan template detail returned by the API."""

    id: uuid.UUID
    name: str
    tagline: str | None
    duration_months: int
    base_price_inr: Decimal
    description: str | None
    features: list[str] | None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Tenant-effective plan view ─────────────────────────────────────────────────

class TenantPlanRead(BaseModel):
    """
    Effective plan as seen by tenants.

    Merges the platform template with any tenant-specific override.
    effective_price_inr = custom_price_inr if has_override else base_price_inr.
    """

    id: uuid.UUID
    name: str
    tagline: str | None
    duration_months: int
    base_price_inr: Decimal
    effective_price_inr: Decimal
    has_override: bool
    description: str | None
    features: list[str] | None
    is_active: bool
    sort_order: int

    model_config = {"from_attributes": True}


# ── Tenant price override ─────────────────────────────────────────────────────

class TenantPlanOverrideUpsert(BaseModel):
    """Payload for PUT /plans/{template_id}/price (tenant ADMIN only)."""

    custom_price_inr: Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)] = Field(
        ...,
        description="Custom price for this plan in this tenant (0 means free).",
        examples=[899.00],
    )
    is_active: bool = True


# ── Member Subscription ───────────────────────────────────────────────────────

class SubscriptionCreate(BaseModel):
    """Payload for POST /subscriptions (tenant ADMIN assigns a plan to a member)."""

    user_id: uuid.UUID = Field(..., description="UUID of the member user to subscribe")
    plan_template_id: uuid.UUID = Field(..., description="UUID of the plan template to assign")
    starts_at: datetime | None = Field(
        None,
        description="Subscription start date/time (UTC). Defaults to now if omitted.",
    )
    notes: str | None = Field(None, max_length=500)


class SubscriptionRead(BaseModel):
    """Full subscription detail returned by the API."""

    id: uuid.UUID
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    plan_template_id: uuid.UUID
    plan_name: str
    plan_tagline: str | None
    duration_months: int
    price_paid_inr: Decimal
    starts_at: datetime
    expires_at: datetime
    status: str
    notes: str | None
    created_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionUpdate(BaseModel):
    """Payload for PATCH /subscriptions/{id} (cancel or update notes)."""

    status: Literal["cancelled"] | None = Field(
        None, description="Only 'cancelled' is accepted; use POST /subscriptions to re-assign."
    )
    notes: str | None = Field(None, max_length=500)
