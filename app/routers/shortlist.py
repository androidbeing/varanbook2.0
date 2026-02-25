"""
routers/shortlist.py – Express interest, accept / reject matches.

Endpoints:
  POST   /shortlists/              – shortlist a profile (express interest)
  GET    /shortlists/sent          – list shortlists sent by current user's profile
  GET    /shortlists/received      – list shortlists received by current user's profile
  PATCH  /shortlists/{id}          – accept or reject
  DELETE /shortlists/{id}          – withdraw (sender only)
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_member
from app.database import get_db
from app.models.profile import Profile
from app.models.shortlist import Shortlist, ShortlistStatus
from app.models.user import User
from app.schemas.shortlist import ShortlistCreate, ShortlistList, ShortlistRead, ShortlistStatusUpdate

router = APIRouter(prefix="/shortlists", tags=["Shortlist / Accept"])


async def _get_caller_profile(
    current_user: User,
    db: "AsyncSession",
) -> Profile:
    """Resolve the Profile for the authenticated user."""
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Create your profile first.")
    return profile


@router.post(
    "/",
    response_model=ShortlistRead,
    status_code=status.HTTP_201_CREATED,
    summary="Express interest in a profile",
)
async def create_shortlist(
    body: ShortlistCreate,
    request: Request,
    db: Annotated["AsyncSession", Depends(get_db)],
    current_user: Annotated[User, Depends(require_member)],
) -> ShortlistRead:
    caller = await _get_caller_profile(current_user, db)

    if caller.id == body.to_profile_id:
        raise HTTPException(status_code=400, detail="Cannot shortlist yourself.")

    # Verify target profile exists in this tenant
    target = await db.get(Profile, body.to_profile_id)
    if not target or target.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Target profile not found.")

    # Duplicate check
    existing = await db.execute(
        select(Shortlist).where(
            Shortlist.from_profile_id == caller.id,
            Shortlist.to_profile_id == body.to_profile_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already shortlisted this profile.")

    entry = Shortlist(
        tenant_id=current_user.tenant_id,
        from_profile_id=caller.id,
        to_profile_id=body.to_profile_id,
        note=body.note,
        status=ShortlistStatus.SHORTLISTED,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return ShortlistRead.model_validate(entry)


@router.get("/sent", response_model=ShortlistList, summary="Shortlists sent by me")
async def list_sent(
    db: Annotated["AsyncSession", Depends(get_db)],
    current_user: Annotated[User, Depends(require_member)],
    skip: int = 0,
    limit: int = 50,
) -> ShortlistList:
    caller = await _get_caller_profile(current_user, db)
    result = await db.execute(
        select(Shortlist)
        .where(Shortlist.from_profile_id == caller.id)
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()
    return ShortlistList(items=[ShortlistRead.model_validate(i) for i in items], total=len(items))


@router.get("/received", response_model=ShortlistList, summary="Shortlists received by me")
async def list_received(
    db: Annotated["AsyncSession", Depends(get_db)],
    current_user: Annotated[User, Depends(require_member)],
    skip: int = 0,
    limit: int = 50,
) -> ShortlistList:
    caller = await _get_caller_profile(current_user, db)
    result = await db.execute(
        select(Shortlist)
        .where(Shortlist.to_profile_id == caller.id)
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()
    return ShortlistList(items=[ShortlistRead.model_validate(i) for i in items], total=len(items))


@router.patch("/{shortlist_id}", response_model=ShortlistRead, summary="Accept or reject")
async def update_shortlist_status(
    shortlist_id: uuid.UUID,
    body: ShortlistStatusUpdate,
    db: Annotated["AsyncSession", Depends(get_db)],
    current_user: Annotated[User, Depends(require_member)],
) -> ShortlistRead:
    entry = await db.get(Shortlist, shortlist_id)
    if not entry or entry.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Shortlist entry not found.")

    caller = await _get_caller_profile(current_user, db)

    # Only the recipient can accept / reject
    if entry.to_profile_id != caller.id:
        raise HTTPException(status_code=403, detail="Only the recipient can update status.")

    if entry.status != ShortlistStatus.SHORTLISTED:
        raise HTTPException(status_code=409, detail="Already responded to this interest.")

    entry.status = body.status
    await db.flush()
    await db.refresh(entry)
    return ShortlistRead.model_validate(entry)


@router.delete("/{shortlist_id}", status_code=204, summary="Withdraw interest")
async def delete_shortlist(
    shortlist_id: uuid.UUID,
    db: Annotated["AsyncSession", Depends(get_db)],
    current_user: Annotated[User, Depends(require_member)],
) -> None:
    entry = await db.get(Shortlist, shortlist_id)
    if not entry or entry.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Shortlist entry not found.")

    caller = await _get_caller_profile(current_user, db)
    if entry.from_profile_id != caller.id:
        raise HTTPException(status_code=403, detail="Only the sender can withdraw.")

    await db.delete(entry)
    await db.flush()
