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

from pydantic import BaseModel, EmailStr, Field, field_validator

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

    # Phase-2 fields
    contact_person: str = Field(..., min_length=2, max_length=200, examples=["Ravi Sharma"])
    contact_number: str = Field(..., examples=["+919876543210"])
    whatsapp_number: str | None = Field(None, examples=["+919876543210"])
    pin: str = Field(..., pattern=r"^\d{6}$", examples=["600001"])
    upi_id: str | None = Field(None, pattern=r"^[\w.\-]+@[\w.\-]+$", examples=["sharma@upi"])
    castes: list[str] = Field(default_factory=list, examples=[["Brahmin", "Iyer"]])

    @field_validator("slug")
    @classmethod
    def slug_must_be_valid(cls, v: str) -> str:
        return _validate_slug(v.lower())

    @field_validator("contact_number", "whatsapp_number")
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

    # Phase-2 optional updates
    contact_person: str | None = Field(None, min_length=2, max_length=200)
    contact_number: str | None = None
    whatsapp_number: str | None = None
    pin: str | None = Field(None, pattern=r"^\d{6}$")
    upi_id: str | None = Field(None, pattern=r"^[\w.\-]+@[\w.\-]+$")
    castes: list[str] | None = None

    @field_validator("contact_number", "whatsapp_number")
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
    castes: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}  # enables ORM mode


class TenantList(BaseModel):
    """Paginated list wrapper."""

    items: list[TenantRead]
    total: int
    page: int
    page_size: int
