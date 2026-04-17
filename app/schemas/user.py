"""
schemas/user.py – Pydantic request/response schemas for User.

Validation rules:
  - password: min 8 chars, must contain uppercase, lowercase, digit, special char
  - email: RFC-5321 via pydantic EmailStr
  - phone: E.164 format
  - role: constrained to allowed values and role-elevation rules enforced in service layer
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models.profile import Gender
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
    avatar_key: str | None = Field(None, max_length=512, description="S3 object key for profile picture")


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


class ForgotPasswordPhoneRequest(BaseModel):
    """POST /auth/forgot-password-phone – verify phone via OTP then return a reset token."""

    phone: str = Field(..., examples=["+919876543210"])
    phone_firebase_token: str = Field(
        ...,
        description="Firebase ID token from phone OTP verification",
    )


class ForgotPasswordPhoneResponse(BaseModel):
    """Reset token returned after successful phone OTP verification.

    The frontend should immediately navigate to /reset-password?token=<reset_token>.
    The token expires in 1 hour.
    """

    reset_token: str


class PasswordResetConfirm(BaseModel):
    """POST /auth/reset-password – set new password with token."""

    token: str = Field(..., min_length=32, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong_new_password(cls, v: str) -> str:
        return _check_password(v)


class OTPLoginRequest(BaseModel):
    """POST /auth/login-otp – sign in using Firebase phone OTP (no password needed).

    The frontend uses the Firebase JS SDK to send an SMS OTP and, on correct
    entry, receives a Firebase ID token.  That token is posted here along with
    the phone number.  The backend verifies the token and issues a JWT pair.
    When FIREBASE_OTP_ENABLED=False (dev mode) token verification is skipped.
    """

    phone: str = Field(..., examples=["+919876543210"])
    phone_firebase_token: str = Field(
        ...,
        description="Firebase ID token from phone OTP verification",
    )

    @field_validator("phone")
    @classmethod
    def phone_must_be_e164(cls, v: str) -> str:
        import re
        if not re.match(r"^\+[1-9]\d{6,14}$", v):
            raise ValueError("Phone number must be in E.164 format, e.g. +919876543210")
        return v


class RefreshRequest(BaseModel):
    """POST /auth/refresh – exchange refresh token."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """POST /auth/logout – revoke a refresh token."""

    refresh_token: str


class LoginRequest(BaseModel):
    """POST /auth/login – supports both email+password and phone+password."""

    email: str | None = None  # lowercased after validation
    phone: str | None = Field(
        None,
        pattern=r"^\+?[1-9]\d{6,14}$",
        examples=["+919876543210"],
    )
    password: str

    @model_validator(mode="after")
    def requires_email_or_phone(self) -> "LoginRequest":
        if not self.email and not self.phone:
            raise ValueError("Provide either email or phone to log in.")
        return self

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str | None) -> str | None:
        return v.strip().lower() if v else None


# ── Response schemas ───────────────────────────────────────────────────────────
class UserRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    email: str | None
    full_name: str
    phone: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    avatar_key: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserList(BaseModel):
    """Paginated list of users returned to tenant admins."""

    items: list[UserRead]
    total: int
    page: int
    page_size: int


# ── Member onboarding schemas ──────────────────────────────────────────────────

class MemberOnboardRequest(BaseModel):
    """Minimal info required for admin-initiated member onboarding.

    Either email or phone (or both) must be provided.
    When only phone is given no invite email is sent; the temp_password is
    returned in the response body and the admin should share it directly.
    """

    full_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(None, pattern=r"^\+?[1-9]\d{6,14}$")
    gender: Gender  # required — set by admin at onboarding and locked for member editing

    @model_validator(mode="after")
    def at_least_one_contact(self) -> "MemberOnboardRequest":
        if not self.email and not self.phone:
            raise ValueError("Provide at least one of email or phone.")
        return self

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: EmailStr | None) -> str | None:
        return v.strip().lower() if v else None


class MemberOnboardResponse(BaseModel):
    """Returned after single-member onboard; includes one-time temp_password."""

    user: UserRead
    temp_password: str  # shown once — member must change on first login


class AdminOnboardRequest(BaseModel):
    """Super-admin-initiated onboarding for a new tenant admin account.

    No password required — a secure temp password is auto-generated and
    emailed to the new admin.
    """

    full_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    phone: str | None = Field(None, pattern=r"^\+?[1-9]\d{6,14}$")
    tenant_id: uuid.UUID

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()


class AdminOnboardResponse(BaseModel):
    """Returned after admin onboarding; temp_password shown once."""

    user: UserRead
    temp_password: str


class BulkOnboardRow(BaseModel):
    """Per-row result from a bulk CSV onboard operation."""

    row: int
    email: str
    status: Literal["created", "skipped", "error"]
    detail: str | None = None


class BulkOnboardResponse(BaseModel):
    """Summary result returned after bulk CSV upload."""

    total: int
    created: int
    skipped: int
    errors: int
    rows: list[BulkOnboardRow]
