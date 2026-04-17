"""
schemas/tenant.py – Pydantic request/response schemas for Tenant.

Validation rules:
  - slug: lowercase alphanumeric + hyphens, 3-100 chars
  - email: RFC-5321 validated via pydantic EmailStr
  - plan must be one of the allowed values
  - max_users / max_admins bounded to sensible ranges
"""

import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

# ── Reusable validators ────────────────────────────────────────────────────────
_E164_RE = re.compile(r"^\+[1-9]\d{6,14}$")
_UPI_RE = re.compile(r"^[\w.\-]+@[\w.\-]+$")
_PIN_RE = re.compile(r"^\d{6}$")


def _validate_e164(v: str | None) -> str | None:
    if v is not None and not _E164_RE.match(v):
        raise ValueError("Phone number must be in E.164 format, e.g. +919876543210")
    return v


# ── Slug validator ────────────────────────────────────────────────────────────
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,98}[a-z0-9]$")


def _validate_slug(v: str) -> str:
    if not _SLUG_RE.match(v):
        raise ValueError(
            "slug must be 3-100 chars, lowercase alphanumeric and hyphens, "
            "and must not start or end with a hyphen"
        )
    return v


# ── Request schemas ────────────────────────────────────────────────────────────
class TenantCreate(BaseModel):
    """Payload for POST /tenants – creates a new matrimonial centre."""

    name: str = Field(..., min_length=2, max_length=200, examples=["Sharma Vivah Kendra"])
    slug: str = Field(..., description="URL-safe unique identifier")
    domain: str | None = Field(None, max_length=255, examples=["sharma.matrimony.in"])
    contact_email: EmailStr
    address: str | None = Field(None, max_length=500)
    plan: Literal["starter", "growth", "enterprise"] = "starter"
    max_users: int = Field(500, ge=10, le=100_000)
    max_admins: int = Field(5, ge=1, le=500)
    can_override_plan_prices: bool = Field(
        False,
        description="When True, the tenant admin may set custom membership plan prices",
    )

    # Phase-2 fields
    contact_person: str = Field(..., min_length=2, max_length=200, examples=["Ravi Sharma"])
    contact_number: str = Field(..., examples=["+919876543210"])
    whatsapp_number: str | None = Field(None, examples=["+919876543210"])
    pin: str = Field(..., pattern=r"^\d{6}$", examples=["600001"])
    upi_id: str | None = Field(None, pattern=r"^[\w.\-]+@[\w.\-]+$", examples=["sharma@upi"])
    upi_name: str | None = Field(None, max_length=200, examples=["Sharma Vivah Kendra"])
    payment_whatsapp: str | None = Field(None, examples=["+919876543210"])
    castes: list[str] = Field(default_factory=list, examples=[["Brahmin", "Iyer"]])
    caste_locked: bool = Field(False, description="When True, members only see profiles of their own caste")
    self_registration_enabled: bool = Field(False, description="When True, members can self-register via /join/<slug>")

    # Optional: bootstrap the first admin user for this tenant in one step
    admin_email: EmailStr | None = Field(
        None,
        description="If provided, an ADMIN user is created for this tenant and a welcome email is dispatched.",
    )
    admin_name: str | None = Field(None, min_length=2, max_length=200)

    @field_validator("slug")
    @classmethod
    def slug_must_be_valid(cls, v: str) -> str:
        return _validate_slug(v.lower())

    @field_validator("contact_number", "whatsapp_number", "payment_whatsapp")
    @classmethod
    def phone_must_be_e164(cls, v: str | None) -> str | None:
        return _validate_e164(v)


class TenantUpdate(BaseModel):
    """Payload for PATCH /tenants/{id} – partial update."""

    name: str | None = Field(None, min_length=2, max_length=200)
    domain: str | None = Field(None, max_length=255)
    contact_email: EmailStr | None = None
    address: str | None = None
    plan: Literal["starter", "growth", "enterprise"] | None = None
    max_users: int | None = Field(None, ge=10, le=100_000)
    max_admins: int | None = Field(None, ge=1, le=500)
    is_active: bool | None = None
    can_override_plan_prices: bool | None = Field(
        None,
        description="Toggle tenant admin ability to set custom plan prices (SuperAdmin only)",
    )

    # Phase-2 optional updates
    contact_person: str | None = Field(None, min_length=2, max_length=200)
    contact_number: str | None = None
    whatsapp_number: str | None = None
    pin: str | None = Field(None, pattern=r"^\d{6}$")
    upi_id: str | None = Field(None, pattern=r"^[\w.\-]+@[\w.\-]+$")
    upi_name: str | None = Field(None, max_length=200)
    payment_whatsapp: str | None = None
    castes: list[str] | None = None
    caste_locked: bool | None = None
    self_registration_enabled: bool | None = None

    @field_validator("contact_number", "whatsapp_number", "payment_whatsapp")
    @classmethod
    def phone_must_be_e164(cls, v: str | None) -> str | None:
        return _validate_e164(v)


# ── Response schemas ───────────────────────────────────────────────────────────
class TenantRead(BaseModel):
    """Public representation of a Tenant returned by the API."""

    id: uuid.UUID
    name: str
    slug: str
    domain: str | None
    contact_email: str
    plan: str
    max_users: int
    max_admins: int
    is_active: bool
    contact_person: str | None
    contact_number: str | None
    whatsapp_number: str | None
    pin: str | None
    upi_id: str | None
    upi_name: str | None = None
    upi_qr_key: str | None = None
    payment_whatsapp: str | None = None
    castes: list[str] | None
    caste_locked: bool = False
    logo_key: str | None = None
    can_override_plan_prices: bool = False
    self_registration_enabled: bool = False
    active_members_count: int = 0
    created_at: datetime
    updated_at: datetime
    # Populated only on tenant creation when admin_email was supplied
    temp_password: str | None = None

    model_config = {"from_attributes": True}  # enables ORM mode


class TenantList(BaseModel):
    """Paginated list wrapper."""

    items: list[TenantRead]
    total: int
    page: int
    page_size: int


class TenantPaymentInfoRead(BaseModel):
    """Payment information shown to members for making payments."""

    upi_id: str | None = None
    upi_name: str | None = None
    upi_qr_key: str | None = None
    payment_whatsapp: str | None = None
    tenant_name: str | None = None

    model_config = {"from_attributes": True}


class TenantPublicInfo(BaseModel):
    """Minimal tenant info returned on the public /join page (no sensitive data)."""

    name: str
    slug: str
    logo_key: str | None = None
    self_registration_enabled: bool = False
    phone_otp_enabled: bool = False

    model_config = {"from_attributes": True}


class SelfRegisterRequest(BaseModel):
    """Payload for public member self-registration via /join/<slug>.

    Either email or phone (or both) must be supplied.
    When FIREBASE_OTP_ENABLED=True, phone must be accompanied by
    phone_firebase_token so the backend can verify OTP ownership.
    When FIREBASE_OTP_ENABLED=False (dev mode) the token field is ignored.
    """

    full_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(
        None,
        examples=["+919876543210"],
        description="E.164 phone number. Required when authenticating via OTP.",
    )
    gender: str = Field(..., description="male or female")
    password: str = Field(..., min_length=8, max_length=128)
    phone_firebase_token: str | None = Field(
        None,
        description="Firebase ID token obtained after phone OTP verification. "
                    "Required when phone is provided and FIREBASE_OTP_ENABLED=true.",
    )

    @model_validator(mode="after")
    def at_least_one_contact(self) -> "SelfRegisterRequest":
        if not self.email and not self.phone:
            raise ValueError("At least one of email or phone must be provided.")
        return self

    @field_validator("phone")
    @classmethod
    def phone_must_be_e164(cls, v: str | None) -> str | None:
        if v is not None and not _E164_RE.match(v):
            raise ValueError("Phone number must be in E.164 format, e.g. +919876543210")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v
