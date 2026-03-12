"""
routers/profiles.py – Matrimonial profile CRUD endpoints.

All endpoints require an authenticated user. Members can only access
their own profile; Admins can access any profile within their tenant.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.profile import Profile, ProfileStatus
from app.models.shortlist import Shortlist, ShortlistStatus
from app.models.user import User, UserRole
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate


def _profile_read(profile: Profile) -> ProfileRead:
    """Build ProfileRead, injecting user.full_name if the relationship is loaded."""
    base = ProfileRead.model_validate(profile)
    try:
        fn = profile.user.full_name if profile.user else None
    except Exception:
        fn = None
    return base.model_copy(update={"full_name": fn}) if fn else base

router = APIRouter(prefix="/profiles", tags=["Matrimonial Profiles"])


def _assert_profile_access(profile: Profile, current_user: User) -> None:
    """
    Raises HTTP 403 if the user has no right to access this profile.

    Rules:
    - SUPER_ADMIN: full access
    - ADMIN: any profile within their tenant
    - MEMBER: their own profile OR any active profile within their tenant
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return
    if current_user.role == UserRole.ADMIN:
        if profile.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied.")
        return
    # MEMBER: own profile always accessible; others must be active and in same tenant
    if profile.user_id == current_user.id:
        return
    if profile.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    if profile.status != ProfileStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="Profile is not publicly visible.")


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

    # Fields present in the schema for backward-compat but absent from the ORM model
    _PROFILE_ORM_EXCLUDE = {"annual_income_inr", "siblings", "nakshatra", "occupation", "education", "about_me", "display_name"}

    profile = Profile(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        status=ProfileStatus.ACTIVE,   # member self-service profiles are active immediately
        **{k: v for k, v in payload.model_dump().items() if k not in _PROFILE_ORM_EXCLUDE},
    )
    db.add(profile)
    await db.flush()
    result_c = await db.execute(
        select(Profile).where(Profile.id == profile.id).options(selectinload(Profile.user))
    )
    return _profile_read(result_c.scalar_one())


@router.get(
    "/",
    response_model=dict,
    summary="Browse profiles in the current tenant",
)
async def list_profiles(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    gender: str | None = Query(None),
    city: str | None = Query(None),
    dhosam: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> dict:
    """
    Browse profiles within the current tenant.

    - MEMBER: sees only 'active' profiles (excluding their own), automatically
      filtered to the opposite gender.
    - ADMIN / SUPER_ADMIN: sees all profiles in their tenant.
    """
    query = select(Profile).where(Profile.tenant_id == current_user.tenant_id)

    # Members only see active profiles and not their own
    if current_user.role == UserRole.MEMBER:
        query = query.where(
            Profile.status == "active",
            Profile.user_id != current_user.id,
        )
        # Auto-filter to opposite gender based on member's own profile
        own_profile_result = await db.execute(
            select(Profile.gender).where(Profile.user_id == current_user.id)
        )
        own_gender = own_profile_result.scalar_one_or_none()
        if own_gender == "male":
            query = query.where(Profile.gender == "female")
        elif own_gender == "female":
            query = query.where(Profile.gender == "male")
        # If own gender unknown or 'other', no auto-filter; honour explicit param
        elif gender:
            query = query.where(Profile.gender == gender)
    else:
        if status:
            query = query.where(Profile.status == status)
        if gender:
            query = query.where(Profile.gender == gender)

    if dhosam:
        query = query.where(Profile.dhosam == dhosam)
    if city:
        query = query.where(Profile.city.ilike(f"%{city}%"))
    if search:
        query = query.join(User, Profile.user_id == User.id).where(
            User.full_name.ilike(f"%{search}%")
        )

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    items_result = await db.execute(
        query.options(selectinload(Profile.user))
        .order_by(Profile.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [_profile_read(p) for p in items_result.scalars().all()]

    pages = max(1, -(-total // size))  # ceiling division
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


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
        .options(selectinload(Profile.user))
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return _profile_read(profile)


@router.patch(
    "/me",
    response_model=ProfileRead,
    summary="Update current user's own profile",
)
async def update_my_profile(
    payload: ProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileRead:
    """Members use this to update their own profile. No profile UUID needed."""
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Create one first.")

    _ORPHAN_FIELDS = {"annual_income_inr", "siblings", "nakshatra", "occupation", "education", "about_me", "display_name"}

    # Lock fields set by admin at onboarding — members cannot overwrite them
    _LOCKED_FIELDS: set[str] = set()
    if profile.gender is not None:
        _LOCKED_FIELDS.add("gender")
    if current_user.phone is not None:
        _LOCKED_FIELDS.add("mobile")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field not in _ORPHAN_FIELDS and field not in _LOCKED_FIELDS and hasattr(profile, field):
            setattr(profile, field, value)

    # Promote draft profiles to active whenever the member saves any section
    if profile.status == ProfileStatus.DRAFT:
        profile.status = ProfileStatus.ACTIVE

    await db.flush()
    result2 = await db.execute(
        select(Profile).where(Profile.id == profile.id).options(selectinload(Profile.user))
    )
    return _profile_read(result2.scalar_one())


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
    result = await db.execute(
        select(Profile).where(Profile.id == profile_id).options(selectinload(Profile.user))
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    # For MEMBER viewers, check for an accepted shortlist connection BEFORE the
    # standard access check so that accepted connections bypass the profile-status
    # restriction (e.g. DRAFT profiles created by an admin are still reachable by
    # the connected member).
    connection_status: str | None = None
    is_accepted_connection = False
    if current_user.role == UserRole.MEMBER and profile.user_id != current_user.id:
        viewer_profile_result = await db.execute(
            select(Profile.id).where(Profile.user_id == current_user.id)
        )
        viewer_profile_id = viewer_profile_result.scalar_one_or_none()
        if viewer_profile_id:
            sl_result = await db.execute(
                select(Shortlist.status).where(
                    or_(
                        (Shortlist.from_profile_id == viewer_profile_id) & (Shortlist.to_profile_id == profile_id),
                        (Shortlist.from_profile_id == profile_id) & (Shortlist.to_profile_id == viewer_profile_id),
                    )
                ).where(Shortlist.status == ShortlistStatus.ACCEPTED).limit(1)
            )
            sl_status = sl_result.scalar_one_or_none()
            if sl_status:
                connection_status = sl_status.value
                is_accepted_connection = True

    if is_accepted_connection:
        # Accepted connections bypass the profile-status restriction, but
        # tenant isolation is still enforced.
        if profile.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied.")
    else:
        _assert_profile_access(profile, current_user)

    read = _profile_read(profile)
    return read.model_copy(update={"connection_status": connection_status})


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

    _ORPHAN_FIELDS = {"annual_income_inr", "siblings", "nakshatra", "occupation", "education", "about_me", "display_name"}
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field not in _ORPHAN_FIELDS and hasattr(profile, field):
            setattr(profile, field, value)

    await db.flush()
    result_u = await db.execute(
        select(Profile).where(Profile.id == profile.id).options(selectinload(Profile.user))
    )
    return _profile_read(result_u.scalar_one())


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
