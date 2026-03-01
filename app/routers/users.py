"""
routers/users.py – User/Admin onboarding + Auth endpoints.

Endpoints:
  POST /auth/login            – obtain JWT pair + persist hashed refresh token
  POST /auth/refresh          – verify DB hash, rotate, return new pair
  POST /auth/logout           – revoke refresh token in DB
  POST /auth/forgot-password  – generate reset token, email link
  POST /auth/reset-password   – validate token, set new password
  POST /auth/change-password  – change password (authenticated)
  POST /users/                – member self-registration
  POST /users/admin           – admin onboarding  POST /users/onboard         – admin: single member onboard (minimal info)
  POST /users/onboard/bulk    – admin: bulk member onboard via CSV upload  GET  /users/members         – list members of the current tenant (admin+)
  GET  /users/me              – current user profile
  PATCH /users/me             – partial update
"""

import csv
import hashlib
import io
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from jose import JWTError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.config import get_settings
from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.refresh_token import RefreshToken
from app.models.password_reset import PasswordResetToken
from app.schemas.user import (
    AdminCreate,
    BulkOnboardResponse,
    BulkOnboardRow,
    LoginRequest,
    LogoutRequest,
    MemberOnboardRequest,
    MemberOnboardResponse,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserList,
    UserRead,
    UserUpdate,
)

settings = get_settings()

# ── Password hashing ───────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt(12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def _sha256(value: str) -> str:
    """SHA-256 hex digest – used for refresh / reset tokens (not passwords)."""
    return hashlib.sha256(value.encode()).hexdigest()


# ── Routers ────────────────────────────────────────────────────────────────────
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/users", tags=["User Management"])


# ────────────────────────────────────────────────────────────────────────────────
# AUTH ENDPOINTS
# ────────────────────────────────────────────────────────────────────────────────
@auth_router.post("/login", response_model=TokenResponse, summary="Obtain JWT pair")
async def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    result = await db.execute(
        select(User).where(User.email == payload.email.lower())
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    user.last_login_at = datetime.now(tz=timezone.utc)

    access = create_access_token(user.id, user.tenant_id, user.role.value)
    raw_refresh = create_refresh_token(user.id, user.tenant_id, user.role.value)

    # Persist hashed refresh token for later verification / rotation
    expires_at = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        if hasattr(settings, "REFRESH_TOKEN_EXPIRE_MINUTES")
        else 60 * 24 * 7
    )
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=_sha256(raw_refresh),
            device_info=request.headers.get("user-agent", "")[:512],
            expires_at=expires_at,
        )
    )
    await db.flush()

    return TokenResponse(
        access_token=access,
        refresh_token=raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@auth_router.post(
    "/refresh", response_model=TokenResponse, summary="Rotate refresh token"
)
async def refresh_token(
    body: RefreshRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    try:
        token_payload = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")

    if token_payload.typ != "refresh":
        raise HTTPException(status_code=401, detail="Provide a refresh token.")

    # Look up the stored token by hash
    token_hash = _sha256(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked.is_(False),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise HTTPException(status_code=401, detail="Refresh token not recognised or revoked.")
    if stored.expires_at < datetime.now(tz=timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token has expired.")

    user = await db.get(User, uuid.UUID(token_payload.sub))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive.")

    # Revoke old token and issue new pair
    stored.is_revoked = True
    stored.last_used_at = datetime.now(tz=timezone.utc)

    new_access = create_access_token(user.id, user.tenant_id, user.role.value)
    new_refresh = create_refresh_token(user.id, user.tenant_id, user.role.value)

    expires_at = stored.expires_at  # keep same window
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=_sha256(new_refresh),
            device_info=request.headers.get("user-agent", "")[:512],
            expires_at=expires_at,
        )
    )
    await db.flush()

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke refresh token")
async def logout(
    body: LogoutRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    token_hash = _sha256(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()
    if stored:
        stored.is_revoked = True
        await db.flush()


@auth_router.post("/forgot-password", status_code=204, summary="Request password reset email")
async def forgot_password(
    body: PasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Always returns 204 to prevent user enumeration.
    If the email exists, we store a reset token and queue an email.
    """
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()
    if user:
        raw_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=_sha256(raw_token),
                expires_at=expires_at,
            )
        )
        await db.flush()
        # Import here to avoid circular deps; email service enqueues async send
        try:
            from app.services.email import EmailService
            await EmailService.send_password_reset(user.email, raw_token)
        except Exception:
            pass  # never surface email errors to caller

    # Deliberate: always 204 (no content)


@auth_router.post("/reset-password", status_code=204, summary="Confirm password reset")
async def reset_password(
    body: PasswordResetConfirm,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    token_hash = _sha256(body.token)
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.is_used.is_(False),
        )
    )
    record = result.scalar_one_or_none()
    if not record or record.expires_at < datetime.now(tz=timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    user = await db.get(User, record.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.hashed_password = hash_password(body.new_password)
    record.is_used = True
    record.used_at = datetime.now(tz=timezone.utc)
    await db.flush()


@auth_router.post("/change-password", status_code=204, summary="Change own password")
async def change_password(
    body: PasswordChange,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    current_user.hashed_password = hash_password(body.new_password)
    await db.flush()


# ────────────────────────────────────────────────────────────────────────────────
# USER ONBOARDING
# ────────────────────────────────────────────────────────────────────────────────
@users_router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Member self-registration",
)
async def register_member(
    payload: UserCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRead:
    tenant: Tenant | None = request.state.tenant
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant context is required.")

    user = User(
        tenant_id=tenant.id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role=UserRole.MEMBER,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered.")

    await db.refresh(user)
    return UserRead.model_validate(user)


@users_router.post(
    "/admin",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Admin onboarding",
)
async def onboard_admin(
    payload: AdminCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> UserRead:
    if (
        current_user.role != UserRole.SUPER_ADMIN
        and current_user.tenant_id != payload.tenant_id
    ):
        raise HTTPException(status_code=403, detail="Cannot create admins for other tenants.")

    tenant = await db.get(Tenant, payload.tenant_id)
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=404, detail="Tenant not found or inactive.")

    user = User(
        tenant_id=payload.tenant_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role=UserRole.ADMIN,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered.")

    await db.refresh(user)
    return UserRead.model_validate(user)


# ────────────────────────────────────────────────────────────────────────────────
# MEMBER ONBOARDING (admin-initiated)
# ────────────────────────────────────────────────────────────────────────────────

@users_router.post(
    "/onboard",
    response_model=MemberOnboardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin: onboard a single member with basic info",
)
async def onboard_member(
    payload: MemberOnboardRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> MemberOnboardResponse:
    """
    Tenant admin creates a member account with minimal info (name + email + optional phone).
    A secure temporary password is auto-generated and returned in the response (visible once).
    An invite email is sent to the member with login instructions.
    The member is expected to log in and complete their profile details afterwards.
    """
    if current_user.tenant_id is None:
        raise HTTPException(status_code=400, detail="Super admins must specify a tenant.")

    temp_password = secrets.token_urlsafe(12)  # 16-char URL-safe string
    user = User(
        tenant_id=current_user.tenant_id,
        email=payload.email,
        hashed_password=hash_password(temp_password),
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

    # Send invite email — never fail the request if email delivery fails
    try:
        from app.services.email import EmailService
        await EmailService.send_member_invite(user.email, temp_password, user.full_name)
    except Exception:
        pass

    return MemberOnboardResponse(
        user=UserRead.model_validate(user),
        temp_password=temp_password,
    )


@users_router.post(
    "/onboard/bulk",
    response_model=BulkOnboardResponse,
    summary="Admin: bulk onboard members via CSV upload",
)
async def onboard_members_bulk(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
    file: UploadFile = File(..., description="CSV file with columns: full_name, email, phone (optional)"),
) -> BulkOnboardResponse:
    """
    Upload a CSV file to onboard multiple members at once.

    Required CSV columns:
        full_name, email
    Optional columns:
        phone

    Each row is processed individually using savepoints so that one duplicate
    email does not abort the entire batch. A per-row status report is returned:
        created  – user account created successfully (invite email queued)
        skipped  – email already exists in the system
        error    – row was malformed (missing required fields)
    """
    if current_user.tenant_id is None:
        raise HTTPException(status_code=400, detail="Super admins must specify a tenant.")

    raw = await file.read()
    try:
        decoded = raw.decode("utf-8-sig")  # handles BOM from Excel exports
    except UnicodeDecodeError:
        decoded = raw.decode("latin-1")

    reader = csv.DictReader(io.StringIO(decoded))

    rows: list[BulkOnboardRow] = []
    created = skipped = errors = 0

    for row_num, record in enumerate(reader, start=1):
        email = (record.get("email") or "").strip().lower()
        full_name = (record.get("full_name") or "").strip()
        phone = (record.get("phone") or "").strip() or None

        if not email or not full_name:
            errors += 1
            rows.append(
                BulkOnboardRow(
                    row=row_num,
                    email=email or "—",
                    status="error",
                    detail="Missing required field: full_name and/or email",
                )
            )
            continue

        temp_password = secrets.token_urlsafe(12)
        user = User(
            tenant_id=current_user.tenant_id,
            email=email,
            hashed_password=hash_password(temp_password),
            full_name=full_name,
            phone=phone,
            role=UserRole.MEMBER,
            is_active=True,
        )

        # Use a savepoint so one IntegrityError doesn't abort the whole batch
        try:
            async with db.begin_nested():
                db.add(user)
                await db.flush()
                await db.refresh(user)

            created += 1
            rows.append(BulkOnboardRow(row=row_num, email=email, status="created"))

            # Send invite email — fire-and-forget
            try:
                from app.services.email import EmailService
                await EmailService.send_member_invite(email, temp_password, full_name)
            except Exception:
                pass

        except IntegrityError:
            skipped += 1
            rows.append(
                BulkOnboardRow(
                    row=row_num,
                    email=email,
                    status="skipped",
                    detail="Email already registered",
                )
            )

    return BulkOnboardResponse(
        total=len(rows),
        created=created,
        skipped=skipped,
        errors=errors,
        rows=rows,
    )


# ────────────────────────────────────────────────────────────────────────────────
# LIST MEMBERS (admin view)
# ────────────────────────────────────────────────────────────────────────────────

@users_router.get(
    "/members",
    response_model=UserList,
    summary="List members of the current tenant (admin only)",
)
async def list_members(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None),
) -> UserList:
    """
    Return paginated list of MEMBER-role users belonging to the caller's tenant.

    - ADMIN sees only their own tenant's members.
    - SUPER_ADMIN must use the /admin/tenants routes; this endpoint always
      scopes to the caller's tenant_id.
    """
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="Super admins have no tenant scope. Use /admin/tenants instead.",
        )

    query = select(User).where(
        User.tenant_id == current_user.tenant_id,
        User.role == UserRole.MEMBER,
    )
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    items_result = await db.execute(
        query.order_by(User.full_name).offset((page - 1) * page_size).limit(page_size)
    )
    items = [UserRead.model_validate(u) for u in items_result.scalars().all()]

    return UserList(items=items, total=total, page=page, page_size=page_size)


# ────────────────────────────────────────────────────────────────────────────────
# CURRENT USER
# ────────────────────────────────────────────────────────────────────────────────
@users_router.get("/me", response_model=UserRead, summary="Get current user info")
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    return UserRead.model_validate(current_user)


@users_router.patch("/me", response_model=UserRead, summary="Update current user")
async def update_me(
    payload: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await db.flush()
    await db.refresh(current_user)
    return UserRead.model_validate(current_user)
