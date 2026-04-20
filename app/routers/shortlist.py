"""
routers/shortlist.py – Express interest, accept / reject matches.

Endpoints:
  POST   /shortlists/                            – shortlist a profile (express interest)
  GET    /shortlists/sent                        – list shortlists sent by current user's profile
  GET    /shortlists/received                    – list shortlists received by current user's profile
  GET    /shortlists/shortlisted-profiles        – paginated Profile objects for shortlisted profiles
  PATCH  /shortlists/{id}                        – accept or reject
  DELETE /shortlists/{id}                        – withdraw (sender only)
  DELETE /shortlists/by-profile/{to_profile_id} – unshortlist by profile ID
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user, require_admin, require_member
from app.database import get_db
from app.models.membership_plan import MemberSubscription, MembershipPlanTemplate, SubscriptionStatus
from app.models.profile import Profile
from app.models.shortlist import Shortlist, ShortlistStatus
from app.models.user import User
from app.schemas.profile import ProfileRead
from app.schemas.shortlist import (
    ShortlistCreate, ShortlistList, ShortlistPairList, ShortlistPairRead,
    ProfileSummary, ShortlistRead, ShortlistStatusUpdate,
    InterestRead, InterestList,
)


def _read_profile(profile: Profile) -> ProfileRead:
    base = ProfileRead.model_validate(profile)
    try:
        fn = profile.user.full_name if profile.user else None
    except Exception:
        fn = None
    return base.model_copy(update={"full_name": fn}) if fn else base

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

    # Interest request limit – enforced per subscription period
    sub_result = await db.execute(
        select(MemberSubscription)
        .where(
            MemberSubscription.user_id == current_user.id,
            MemberSubscription.tenant_id == current_user.tenant_id,
            MemberSubscription.status == SubscriptionStatus.ACTIVE,
        )
        .order_by(MemberSubscription.created_at.desc())
        .limit(1)
    )
    active_sub = sub_result.scalar_one_or_none()
    if active_sub:
        plan = await db.get(MembershipPlanTemplate, active_sub.plan_template_id)
        if plan and plan.max_interests is not None:
            sent_count_result = await db.execute(
                select(func.count()).select_from(Shortlist).where(
                    Shortlist.from_profile_id == caller.id,
                    Shortlist.created_at >= active_sub.starts_at,
                )
            )
            sent_count = sent_count_result.scalar_one()
            if sent_count >= plan.max_interests:
                raise HTTPException(
                    status_code=429,
                    detail=(
                        f"You have reached the {plan.max_interests} interest request limit "
                        f"for your {plan.name} plan. Upgrade to send more."
                    ),
                )

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

    # Notify the recipient — fire-and-forget
    try:
        from app.services.email import EmailService
        target_user = await db.get(User, target.user_id)
        if target_user and target_user.email:
            sender_name = current_user.full_name or "Someone"
            await EmailService.send_shortlist_notification(target_user.email, sender_name)
    except Exception:
        pass

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


@router.get(
    "/admin/pairs",
    response_model=ShortlistPairList,
    summary="[Admin] List all shortlist pairs in this tenant",
)
async def admin_list_pairs(
    db: Annotated["AsyncSession", Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> ShortlistPairList:
    query = (
        select(Shortlist)
        .where(Shortlist.tenant_id == current_user.tenant_id)
        .options(
            selectinload(Shortlist.from_profile).selectinload(Profile.user),
            selectinload(Shortlist.to_profile).selectinload(Profile.user),
        )
    )
    if status_filter:
        query = query.where(Shortlist.status == status_filter)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    items_result = await db.execute(
        query.order_by(Shortlist.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    def _pair(entry: Shortlist) -> ShortlistPairRead:
        def _summary(p: Profile) -> ProfileSummary:
            fn = None
            try:
                fn = p.user.full_name if p.user else None
            except Exception:
                pass
            dob = p.date_of_birth.isoformat() if p.date_of_birth else None
            return ProfileSummary(
                id=p.id, full_name=fn, gender=p.gender,
                date_of_birth=dob, city=p.city, state=p.state,
            )
        return ShortlistPairRead(
            id=entry.id,
            from_profile=_summary(entry.from_profile),
            to_profile=_summary(entry.to_profile),
            status=entry.status,
            note=entry.note,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )

    items = [_pair(e) for e in items_result.scalars().all()]
    pages = max(1, -(-total // size))
    return ShortlistPairList(items=items, total=total, page=page, size=size, pages=pages)


@router.get(
    "/shortlisted-profiles",
    response_model=dict,
    summary="Browse shortlisted profiles (paginated, same shape as GET /profiles/)",
)
async def list_shortlisted_profiles(
    db: Annotated["AsyncSession", Depends(get_db)],
    current_user: Annotated[User, Depends(require_member)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> dict:
    caller = await _get_caller_profile(current_user, db)

    subq = select(Shortlist.to_profile_id).where(Shortlist.from_profile_id == caller.id)
    query = select(Profile).where(Profile.id.in_(subq))

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    items_result = await db.execute(
        query.options(selectinload(Profile.user))
        .order_by(Profile.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [_read_profile(p) for p in items_result.scalars().all()]
    pages = max(1, -(-total // size))
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.delete(
    "/by-profile/{to_profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unshortlist a profile by its ID (sender only)",
)
async def delete_shortlist_by_profile(
    to_profile_id: uuid.UUID,
    db: Annotated["AsyncSession", Depends(get_db)],
    current_user: Annotated[User, Depends(require_member)],
) -> None:
    caller = await _get_caller_profile(current_user, db)
    result = await db.execute(
        select(Shortlist).where(
            Shortlist.from_profile_id == caller.id,
            Shortlist.to_profile_id == to_profile_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Shortlist entry not found.")
    await db.delete(entry)
    await db.flush()


@router.get(
    "/sent-interests",
    response_model=InterestList,
    summary="Interests sent by me – with full profile of the recipient and current status",
)
async def list_sent_interests(
    db: Annotated["AsyncSession", Depends(get_db)],
    current_user: Annotated[User, Depends(require_member)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> InterestList:
    caller = await _get_caller_profile(current_user, db)

    query = (
        select(Shortlist)
        .where(Shortlist.from_profile_id == caller.id)
        .options(selectinload(Shortlist.to_profile).selectinload(Profile.user))
        .order_by(Shortlist.created_at.desc())
    )
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    rows = (await db.execute(query.offset((page - 1) * size).limit(size))).scalars().all()
    items = [
        InterestRead(
            shortlist_id=r.id,
            status=r.status,
            note=r.note,
            created_at=r.created_at,
            profile=_read_profile(r.to_profile),
        )
        for r in rows
    ]
    pages = max(1, -(-total // size))
    return InterestList(items=items, total=total, page=page, size=size, pages=pages)


@router.get(
    "/received-interests",
    response_model=InterestList,
    summary="Interests received by me – with full profile of the sender and current status",
)
async def list_received_interests(
    db: Annotated["AsyncSession", Depends(get_db)],
    current_user: Annotated[User, Depends(require_member)],
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> InterestList:
    caller = await _get_caller_profile(current_user, db)

    query = (
        select(Shortlist)
        .where(Shortlist.to_profile_id == caller.id)
        .options(selectinload(Shortlist.from_profile).selectinload(Profile.user))
        .order_by(Shortlist.created_at.desc())
    )
    if status_filter:
        query = query.where(Shortlist.status == status_filter)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    rows = (await db.execute(query.offset((page - 1) * size).limit(size))).scalars().all()
    items = [
        InterestRead(
            shortlist_id=r.id,
            status=r.status,
            note=r.note,
            created_at=r.created_at,
            profile=_read_profile(r.from_profile),
        )
        for r in rows
    ]
    pages = max(1, -(-total // size))
    return InterestList(items=items, total=total, page=page, size=size, pages=pages)


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

    # Notify the original sender when their interest is accepted — fire-and-forget
    if body.status == ShortlistStatus.ACCEPTED:
        try:
            from app.services.email import EmailService
            from_profile = await db.get(Profile, entry.from_profile_id)
            if from_profile:
                sender_user = await db.get(User, from_profile.user_id)
                if sender_user and sender_user.email:
                    acceptor_name = current_user.full_name or "Someone"
                    await EmailService.send_accept_notification(sender_user.email, acceptor_name)
        except Exception:
            pass

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
