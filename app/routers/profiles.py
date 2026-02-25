"""
routers/profiles.py – Matrimonial profile CRUD endpoints.

All endpoints require an authenticated user. Members can only access
their own profile; Admins can access any profile within their tenant.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.profile import Profile
from app.models.user import User, UserRole
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate

router = APIRouter(prefix="/profiles", tags=["Matrimonial Profiles"])


def _assert_profile_access(profile: Profile, current_user: User) -> None:
    """
    Raises HTTP 403 if the user has no right to access this profile.

    Rules:
    - SUPER_ADMIN: full access
    - ADMIN: only profiles in their own tenant
    - MEMBER: only their own profile
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return
    if current_user.role == UserRole.ADMIN:
        if profile.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied.")
        return
    # MEMBER
    if profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")


@router.post(
    "/",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create matrimonial profile for the current user",
)
async def create_profile(
    payload: ProfileCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileRead:
    """
    Create a biodata profile.

    One profile per user (unique constraint on user_id).
    """
    # Check if profile already exists
    existing = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail="Profile already exists for this user."
        )

    profile = Profile(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        **payload.model_dump(),
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return ProfileRead.model_validate(profile)


@router.get(
    "/",
    response_model=list[ProfileRead],
    summary="List profiles in the current tenant (admin only)",
)
async def list_profiles(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
    gender: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> list[ProfileRead]:
    """Return paginated profiles within the current admin's tenant."""
    query = select(Profile).where(Profile.tenant_id == current_user.tenant_id)

    if gender:
        query = query.where(Profile.gender == gender)
    if status:
        query = query.where(Profile.status == status)

    result = await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )
    return [ProfileRead.model_validate(p) for p in result.scalars().all()]


@router.get(
    "/me",
    response_model=ProfileRead,
    summary="Get current user's profile",
)
async def get_my_profile(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileRead:
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return ProfileRead.model_validate(profile)


@router.get(
    "/{profile_id}",
    response_model=ProfileRead,
    summary="Get a profile by ID",
)
async def get_profile(
    profile_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileRead:
    profile = await db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    _assert_profile_access(profile, current_user)
    return ProfileRead.model_validate(profile)


@router.patch(
    "/{profile_id}",
    response_model=ProfileRead,
    summary="Update a matrimonial profile",
)
async def update_profile(
    profile_id: uuid.UUID,
    payload: ProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileRead:
    profile = await db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    _assert_profile_access(profile, current_user)

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    await db.flush()
    await db.refresh(profile)
    return ProfileRead.model_validate(profile)


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a matrimonial profile",
)
async def delete_profile(
    profile_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> None:
    """Only admins or super-admins can permanently delete a profile."""
    profile = await db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    _assert_profile_access(profile, current_user)
    await db.delete(profile)
    await db.flush()
