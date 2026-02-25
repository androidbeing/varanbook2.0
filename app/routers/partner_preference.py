"""
routers/partner_preference.py – Manage partner search preferences.

Endpoints:
  PUT  /profiles/{profile_id}/preferences  – upsert (idempotent)
  GET  /profiles/{profile_id}/preferences  – read
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_member
from app.database import get_db
from app.models.partner_preference import PartnerPreference
from app.models.profile import Profile
from app.models.user import User, UserRole
from app.schemas.partner_preference import PartnerPreferenceRead, PartnerPreferenceUpsert

router = APIRouter(tags=["Partner Preferences"])


async def _get_profile_authorised(
    profile_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
    *,
    write: bool = False,
) -> Profile:
    """Fetch profile; enforce same-tenant and (for writes) ownership."""
    profile = await db.get(Profile, profile_id)
    if not profile or profile.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Profile not found.")
    if write and profile.user_id != current_user.id and current_user.role not in (
        UserRole.ADMIN, UserRole.SUPER_ADMIN
    ):
        raise HTTPException(status_code=403, detail="Not your profile.")
    return profile


@router.put(
    "/profiles/{profile_id}/preferences",
    response_model=PartnerPreferenceRead,
    status_code=status.HTTP_200_OK,
    summary="Upsert partner preferences",
)
async def upsert_preferences(
    profile_id: uuid.UUID,
    body: PartnerPreferenceUpsert,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_member)],
) -> PartnerPreferenceRead:
    await _get_profile_authorised(profile_id, current_user, db, write=True)

    result = await db.execute(
        select(PartnerPreference).where(PartnerPreference.profile_id == profile_id)
    )
    pref = result.scalar_one_or_none()

    data = body.model_dump()
    if pref is None:
        pref = PartnerPreference(profile_id=profile_id, **data)
        db.add(pref)
    else:
        for k, v in data.items():
            setattr(pref, k, v)

    await db.flush()
    await db.refresh(pref)
    return PartnerPreferenceRead.model_validate(pref)


@router.get(
    "/profiles/{profile_id}/preferences",
    response_model=PartnerPreferenceRead,
    summary="Get partner preferences",
)
async def get_preferences(
    profile_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_member)],
) -> PartnerPreferenceRead:
    await _get_profile_authorised(profile_id, current_user, db)

    result = await db.execute(
        select(PartnerPreference).where(PartnerPreference.profile_id == profile_id)
    )
    pref = result.scalar_one_or_none()
    if not pref:
        raise HTTPException(status_code=404, detail="No preferences set yet.")
    return PartnerPreferenceRead.model_validate(pref)
