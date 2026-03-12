"""
routers/membership_plans.py – Membership plan endpoints.

Plan hierarchy:
  SuperAdmin  → create / update platform plan templates
  Tenant ADMIN → view effective plans, optionally override prices, assign to members
  MEMBER       → view own active subscription + available plans

Catchy plan names (seeded in migration 008):
  Spark   (3 months)  ₹999  – First connections ignite here
  Bloom   (6 months)  ₹1799 – Love grows in full season
  Eternal (12 months) ₹2999 – A bond that lasts forever
"""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user, require_admin, require_super_admin
from app.database import get_db
from app.models.membership_plan import (
    MembershipPlanTemplate,
    MemberSubscription,
    SubscriptionStatus,
    TenantPlanOverride,
)
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.schemas.membership_plan import (
    PlanTemplateCreate,
    PlanTemplateRead,
    PlanTemplateUpdate,
    SubscriptionCreate,
    SubscriptionRead,
    SubscriptionUpdate,
    TenantPlanOverrideUpsert,
    TenantPlanRead,
)

# ── Routers ───────────────────────────────────────────────────────────────────
# SuperAdmin-scoped endpoints live on a separate prefix so they don't clash
# with tenant-scoped /plans routes.
admin_router = APIRouter(prefix="/admin/plan-templates", tags=["Membership Plans – Admin"])
router = APIRouter(tags=["Membership Plans"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _subscription_read(sub: MemberSubscription) -> SubscriptionRead:
    """Build SubscriptionRead, merging plan template fields."""
    plan = sub.plan_template
    return SubscriptionRead(
        id=sub.id,
        user_id=sub.user_id,
        tenant_id=sub.tenant_id,
        plan_template_id=sub.plan_template_id,
        plan_name=plan.name if plan else "",
        plan_tagline=plan.tagline if plan else None,
        duration_months=plan.duration_months if plan else 0,
        price_paid_inr=Decimal(str(sub.price_paid_inr)),
        starts_at=sub.starts_at,
        expires_at=sub.expires_at,
        status=sub.status.value,
        notes=sub.notes,
        created_by_id=sub.created_by_id,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
    )


def _add_months(dt: datetime, months: int) -> datetime:
    """Add calendar months to a datetime, clamping day on short months."""
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
                        else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return dt.replace(year=year, month=month, day=day)


# ── SuperAdmin: Plan Template CRUD ────────────────────────────────────────────

@admin_router.get(
    "/",
    response_model=list[PlanTemplateRead],
    summary="List all platform plan templates (SuperAdmin)",
)
async def list_plan_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_super_admin)],
    include_inactive: bool = Query(False),
) -> list[PlanTemplateRead]:
    query = select(MembershipPlanTemplate).order_by(MembershipPlanTemplate.sort_order)
    if not include_inactive:
        query = query.where(MembershipPlanTemplate.is_active.is_(True))
    result = await db.execute(query)
    return [PlanTemplateRead.model_validate(t) for t in result.scalars().all()]


@admin_router.post(
    "/",
    response_model=PlanTemplateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a platform plan template (SuperAdmin)",
)
async def create_plan_template(
    payload: PlanTemplateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_super_admin)],
) -> PlanTemplateRead:
    # Enforce unique duration to avoid accidental duplicates at the same tier
    existing = await db.execute(
        select(MembershipPlanTemplate).where(
            MembershipPlanTemplate.duration_months == payload.duration_months
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A plan template with duration_months={payload.duration_months} already exists.",
        )

    template = MembershipPlanTemplate(
        **payload.model_dump(),
        base_price_inr=float(payload.base_price_inr),
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return PlanTemplateRead.model_validate(template)


@admin_router.patch(
    "/{template_id}",
    response_model=PlanTemplateRead,
    summary="Update a platform plan template (SuperAdmin) – duration_months is immutable",
)
async def update_plan_template(
    template_id: uuid.UUID,
    payload: PlanTemplateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_super_admin)],
) -> PlanTemplateRead:
    template = await db.get(MembershipPlanTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Plan template not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "base_price_inr" and value is not None:
            value = float(value)
        setattr(template, field, value)

    await db.flush()
    await db.refresh(template)
    return PlanTemplateRead.model_validate(template)


# ── Tenant-scoped: effective plans ────────────────────────────────────────────

@router.get(
    "/plans",
    response_model=list[TenantPlanRead],
    summary="List effective membership plans for this tenant",
)
async def list_effective_plans(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[TenantPlanRead]:
    """
    Returns all active platform plan templates, with the tenant's custom price
    applied wherever an override exists.

    Available to any authenticated user so members can see plan options.
    """
    templates_result = await db.execute(
        select(MembershipPlanTemplate)
        .where(MembershipPlanTemplate.is_active.is_(True))
        .order_by(MembershipPlanTemplate.sort_order)
    )
    templates = templates_result.scalars().all()

    # Load overrides for this tenant in one query
    overrides: dict[uuid.UUID, TenantPlanOverride] = {}
    if current_user.tenant_id:
        ovr_result = await db.execute(
            select(TenantPlanOverride).where(
                TenantPlanOverride.tenant_id == current_user.tenant_id,
                TenantPlanOverride.is_active.is_(True),
            )
        )
        for ovr in ovr_result.scalars().all():
            overrides[ovr.plan_template_id] = ovr

    plans: list[TenantPlanRead] = []
    for t in templates:
        ovr = overrides.get(t.id)
        has_override = ovr is not None and ovr.custom_price_inr is not None
        effective_price = (
            Decimal(str(ovr.custom_price_inr))
            if has_override
            else Decimal(str(t.base_price_inr))
        )
        plans.append(
            TenantPlanRead(
                id=t.id,
                name=t.name,
                tagline=t.tagline,
                duration_months=t.duration_months,
                base_price_inr=Decimal(str(t.base_price_inr)),
                effective_price_inr=effective_price,
                has_override=has_override,
                description=t.description,
                features=t.features,
                is_active=t.is_active,
                sort_order=t.sort_order,
            )
        )
    return plans


@router.put(
    "/plans/{template_id}/price",
    response_model=TenantPlanRead,
    summary="Override the price of a plan for this tenant (tenant ADMIN only)",
)
async def override_plan_price(
    template_id: uuid.UUID,
    payload: TenantPlanOverrideUpsert,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> TenantPlanRead:
    """
    Allows a tenant admin to set a tenant-specific price for a platform plan.

    Requires the tenant to have `can_override_plan_prices = True` (set by SuperAdmin).
    SuperAdmin can call this on any tenant but is not typical; they manage base prices
    via PATCH /admin/plan-templates/{id} instead.
    """
    # Verify permission — SuperAdmins bypass this check
    if current_user.role != UserRole.SUPER_ADMIN:
        tenant = await db.get(Tenant, current_user.tenant_id)
        if not tenant or not tenant.can_override_plan_prices:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Your tenant is not permitted to override plan prices. "
                    "Contact the platform administrator."
                ),
            )

    template = await db.get(MembershipPlanTemplate, template_id)
    if not template or not template.is_active:
        raise HTTPException(status_code=404, detail="Plan template not found.")

    # Upsert the override
    ovr_result = await db.execute(
        select(TenantPlanOverride).where(
            TenantPlanOverride.tenant_id == current_user.tenant_id,
            TenantPlanOverride.plan_template_id == template_id,
        )
    )
    ovr = ovr_result.scalar_one_or_none()
    if ovr:
        ovr.custom_price_inr = float(payload.custom_price_inr)
        ovr.is_active = payload.is_active
    else:
        ovr = TenantPlanOverride(
            tenant_id=current_user.tenant_id,
            plan_template_id=template_id,
            custom_price_inr=float(payload.custom_price_inr),
            is_active=payload.is_active,
        )
        db.add(ovr)

    await db.flush()

    effective_price = Decimal(str(ovr.custom_price_inr)) if ovr.custom_price_inr is not None else Decimal(str(template.base_price_inr))
    return TenantPlanRead(
        id=template.id,
        name=template.name,
        tagline=template.tagline,
        duration_months=template.duration_months,
        base_price_inr=Decimal(str(template.base_price_inr)),
        effective_price_inr=effective_price,
        has_override=ovr.custom_price_inr is not None,
        description=template.description,
        features=template.features,
        is_active=template.is_active,
        sort_order=template.sort_order,
    )


# ── Subscriptions ─────────────────────────────────────────────────────────────

@router.get(
    "/subscriptions/me",
    response_model=SubscriptionRead | None,
    summary="Get the current user's active subscription",
)
async def get_my_subscription(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SubscriptionRead | None:
    """Returns the most recent active subscription for the authenticated member."""
    result = await db.execute(
        select(MemberSubscription)
        .where(
            MemberSubscription.user_id == current_user.id,
            MemberSubscription.tenant_id == current_user.tenant_id,
            MemberSubscription.status == SubscriptionStatus.ACTIVE,
        )
        .options(selectinload(MemberSubscription.plan_template))
        .order_by(MemberSubscription.created_at.desc())
        .limit(1)
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        return None
    # Lazy expiry: if the hourly background sweep hasn't run yet but the
    # subscription has already passed its expires_at, mark it now so the
    # member always receives an accurate response.
    now = datetime.now(timezone.utc)
    expires = sub.expires_at if sub.expires_at.tzinfo else sub.expires_at.replace(tzinfo=timezone.utc)
    if expires < now:
        sub.status = SubscriptionStatus.EXPIRED
        await db.commit()
        return None
    return _subscription_read(sub)


@router.get(
    "/subscriptions",
    response_model=dict,
    summary="List subscriptions in this tenant (ADMIN)",
)
async def list_subscriptions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
    status_filter: str | None = Query(None, alias="status"),
    user_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> dict:
    from sqlalchemy import func

    query = (
        select(MemberSubscription)
        .where(MemberSubscription.tenant_id == current_user.tenant_id)
        .options(selectinload(MemberSubscription.plan_template))
    )
    if status_filter:
        try:
            query = query.where(MemberSubscription.status == SubscriptionStatus(status_filter))
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status value. Use one of: {[s.value for s in SubscriptionStatus]}",
            )
    if user_id:
        query = query.where(MemberSubscription.user_id == user_id)

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar_one()

    items_result = await db.execute(
        query.order_by(MemberSubscription.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [_subscription_read(s) for s in items_result.scalars().all()]
    pages = max(1, -(-total // size))
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.post(
    "/subscriptions",
    response_model=SubscriptionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a membership plan to a member (ADMIN)",
)
async def create_subscription(
    payload: SubscriptionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> SubscriptionRead:
    """
    Assigns a plan to a member. Automatically computes expires_at from
    starts_at + plan.duration_months. Captures the effective price as a
    billing-history snapshot.
    """
    # Verify the target user belongs to this tenant
    from sqlalchemy import select as _select
    from app.models.user import User as _User

    user_result = await db.execute(
        _select(_User).where(
            _User.id == payload.user_id,
            _User.tenant_id == current_user.tenant_id,
        )
    )
    target_user = user_result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Member not found in this tenant.")

    # Block duplicate active subscriptions for the same member in this tenant
    existing_result = await db.execute(
        select(MemberSubscription).where(
            MemberSubscription.user_id == payload.user_id,
            MemberSubscription.tenant_id == current_user.tenant_id,
            MemberSubscription.status == SubscriptionStatus.ACTIVE,
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=(
                "This member already has an active subscription. "
                "Cancel it before assigning a new plan."
            ),
        )

    template = await db.get(MembershipPlanTemplate, payload.plan_template_id)
    if not template or not template.is_active:
        raise HTTPException(status_code=404, detail="Plan template not found.")

    # Resolve effective price (tenant override if present)
    ovr_result = await db.execute(
        select(TenantPlanOverride).where(
            TenantPlanOverride.tenant_id == current_user.tenant_id,
            TenantPlanOverride.plan_template_id == template.id,
            TenantPlanOverride.is_active.is_(True),
        )
    )
    ovr = ovr_result.scalar_one_or_none()
    effective_price = (
        ovr.custom_price_inr
        if (ovr and ovr.custom_price_inr is not None)
        else template.base_price_inr
    )

    starts_at = payload.starts_at or datetime.now(timezone.utc)
    expires_at = _add_months(starts_at, template.duration_months)

    sub = MemberSubscription(
        user_id=payload.user_id,
        tenant_id=current_user.tenant_id,
        plan_template_id=template.id,
        price_paid_inr=float(effective_price),
        starts_at=starts_at,
        expires_at=expires_at,
        status=SubscriptionStatus.ACTIVE,
        notes=payload.notes,
        created_by_id=current_user.id,
    )
    db.add(sub)
    await db.flush()

    result = await db.execute(
        select(MemberSubscription)
        .where(MemberSubscription.id == sub.id)
        .options(selectinload(MemberSubscription.plan_template))
    )
    return _subscription_read(result.scalar_one())


@router.patch(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionRead,
    summary="Cancel a subscription or update notes (ADMIN)",
)
async def update_subscription(
    subscription_id: uuid.UUID,
    payload: SubscriptionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> SubscriptionRead:
    result = await db.execute(
        select(MemberSubscription)
        .where(
            MemberSubscription.id == subscription_id,
            MemberSubscription.tenant_id == current_user.tenant_id,
        )
        .options(selectinload(MemberSubscription.plan_template))
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")

    if payload.status is not None:
        sub.status = SubscriptionStatus(payload.status)
    if payload.notes is not None:
        sub.notes = payload.notes

    await db.flush()
    await db.refresh(sub)
    return _subscription_read(sub)
