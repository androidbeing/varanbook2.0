"""
schemas/user.py – Pydantic request/response schemas for User.

Validation rules:
  - password: min 8 chars, must contain uppercase, lowercase, digit, special char
  - email: RFC-5321 via pydantic EmailStr
  - phone: E.164 format
  - role: constrained to allowed values and role-elevation rules enforced in service layer
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


# ── Password strength validator ────────────────────────────────────────────────
def _check_password(v: str) -> str:
    errors = []
    if len(v) < 8:
        errors.append("at least 8 characters")
    if not any(c.isupper() for c in v):
        errors.append("one uppercase letter")
    if not any(c.islower() for c in v):
        errors.append("one lowercase letter")
    if not any(c.isdigit() for c in v):
        errors.append("one digit")
    if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in v):
        errors.append("one special character (!@#$%^&*…)")
    if errors:
        raise ValueError("Password must contain: " + ", ".join(errors))
    return v


# ── Request schemas ────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    """Payload for registering a new member / admin."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: str | None = Field(
        None,
        pattern=r"^\+?[1-9]\d{6,14}$",
        examples=["+919876543210"],
    )
    role: UserRole = UserRole.MEMBER  # caller may override; service enforces permissions

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return _check_password(v)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower().strip()


class AdminCreate(UserCreate):
    """Admin onboarding – role is always ADMIN; tenant_id required."""

    role: UserRole = UserRole.ADMIN
    tenant_id: uuid.UUID  # must match the resolved tenant from middleware


class UserUpdate(BaseModel):
    """Partial update – every field is optional."""

    full_name: str | None = Field(None, min_length=2, max_length=200)
    phone: str | None = Field(None, pattern=r"^\+?[1-9]\d{6,14}$")
    fcm_token: str | None = Field(None, max_length=512)
    is_active: bool | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong_new_password(cls, v: str) -> str:
        return _check_password(v)


class PasswordResetRequest(BaseModel):
    """POST /auth/forgot-password – send reset email."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """POST /auth/reset-password – set new password with token."""

    token: str = Field(..., min_length=32, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong_new_password(cls, v: str) -> str:
        return _check_password(v)


class RefreshRequest(BaseModel):
    """POST /auth/refresh – exchange refresh token."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """POST /auth/logout – revoke a refresh token."""

    refresh_token: str


class LoginRequest(BaseModel):
    email: str  # plain str — no RFC validation on login; looked up as-is after lowercasing
    password: str

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()


# ── Response schemas ───────────────────────────────────────────────────────────
class UserRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    email: str
    full_name: str
    phone: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
