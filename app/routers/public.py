"""
routers/public.py – Unauthenticated endpoints for self-registration
                    + admin toggle for self-registration.

Endpoints:
  GET  /public/tenant/{slug}     – minimal tenant info for the /join page
  POST /public/register/{slug}   – member self-registration
  GET  /self-registration/status – current toggle state (admin)
  PUT  /self-registration/status – enable/disable self-registration (admin)
"""

import logging
from typing import Annotated

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models.profile import Profile, ProfileStatus
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.schemas.tenant import SelfRegisterRequest, TenantPublicInfo
from app.schemas.user import UserRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["Public"])
self_reg_router = APIRouter(prefix="/self-registration", tags=["Self-Registration"])


def _hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt(12)).decode()


async def _get_tenant_by_slug(
    slug: str, db: AsyncSession
) -> Tenant:
    """Fetch an active tenant by slug or raise 404."""
    result = await db.execute(
        select(Tenant).where(Tenant.slug == slug.lower(), Tenant.is_active.is_(True))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Centre not found.")
    return tenant


@router.get(
    "/tenant/{slug}",
    response_model=TenantPublicInfo,
    summary="Public tenant info for the join page",
)
async def get_public_tenant(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TenantPublicInfo:
    tenant = await _get_tenant_by_slug(slug, db)
    return TenantPublicInfo.model_validate(tenant)


@router.post(
    "/register/{slug}",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Member self-registration via shareable link",
)
async def self_register(
    slug: str,
    payload: SelfRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRead:
    tenant = await _get_tenant_by_slug(slug, db)

    if not tenant.self_registration_enabled:
        raise HTTPException(
            status_code=403,
            detail="Self-registration is currently disabled for this centre.",
        )

    # Create the member user
    user = User(
        tenant_id=tenant.id,
        email=payload.email.lower(),
        hashed_password=_hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role=UserRole.MEMBER,
        is_active=True,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered.")

    await db.refresh(user)

    # Pre-create profile with gender (same pattern as admin onboard)
    profile = Profile(
        user_id=user.id,
        tenant_id=user.tenant_id,
        gender=payload.gender,
        mobile=user.phone,
        status=ProfileStatus.ACTIVE,
    )
    db.add(profile)
    try:
        await db.flush()
    except Exception:
        pass  # profile creation should not block the user record

    return UserRead.model_validate(user)


# ────────────────────────────────────────────────────────────────────────────────
# ADMIN: Toggle self-registration for own tenant
# ────────────────────────────────────────────────────────────────────────────────

class SelfRegistrationStatus(BaseModel):
    enabled: bool
    join_url_slug: str | None = None


@self_reg_router.get(
    "/status",
    response_model=SelfRegistrationStatus,
    summary="Get self-registration status for current tenant",
)
async def get_self_registration_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> SelfRegistrationStatus:
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant.")
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    return SelfRegistrationStatus(
        enabled=tenant.self_registration_enabled,
        join_url_slug=tenant.slug,
    )


@self_reg_router.put(
    "/status",
    response_model=SelfRegistrationStatus,
    summary="Enable or disable self-registration (admin)",
)
async def set_self_registration_status(
    body: SelfRegistrationStatus,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> SelfRegistrationStatus:
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant.")
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    tenant.self_registration_enabled = body.enabled
    await db.flush()
    await db.refresh(tenant)
    return SelfRegistrationStatus(
        enabled=tenant.self_registration_enabled,
        join_url_slug=tenant.slug,
    )
