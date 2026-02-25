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
  POST /users/admin           – admin onboarding
  GET  /users/me              – current user profile
  PATCH /users/me             – partial update
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
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
    LoginRequest,
    LogoutRequest,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
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
