"""
schemas/shortlist.py – Pydantic schemas for the shortlist / accept flow.

States:
  shortlisted → accepted | rejected
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.shortlist import ShortlistStatus
from app.schemas.profile import ProfileRead


class ShortlistCreate(BaseModel):
    """POST /shortlists – express interest in a profile."""

    to_profile_id: uuid.UUID
    note: str | None = Field(None, max_length=500)


class ShortlistStatusUpdate(BaseModel):
    """PATCH /shortlists/{id} – accept or reject an expression of interest."""

    status: ShortlistStatus


class ShortlistRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    from_profile_id: uuid.UUID
    to_profile_id: uuid.UUID
    status: ShortlistStatus
    note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShortlistList(BaseModel):
    items: list[ShortlistRead]
    total: int


class ProfileSummary(BaseModel):
    """Lightweight profile summary embedded in admin pair view."""
    id: uuid.UUID
    full_name: str | None = None
    gender: str | None = None
    date_of_birth: str | None = None
    city: str | None = None
    state: str | None = None

    model_config = {"from_attributes": True}


class ShortlistPairRead(BaseModel):
    """Admin view of a shortlist pair with embedded profile summaries."""
    id: uuid.UUID
    from_profile: ProfileSummary
    to_profile: ProfileSummary
    status: ShortlistStatus
    note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShortlistPairList(BaseModel):
    items: list[ShortlistPairRead]
    total: int
    page: int
    size: int
    pages: int


class InterestRead(BaseModel):
    """A shortlist entry enriched with the counterpart's full profile.

    Used by:
      GET /shortlists/sent-interests     → profile = to_profile (recipient)
      GET /shortlists/received-interests → profile = from_profile (sender)
    """

    shortlist_id: uuid.UUID
    status: ShortlistStatus
    note: str | None
    created_at: datetime
    profile: ProfileRead


class InterestList(BaseModel):
    items: list[InterestRead]
    total: int
    page: int
    size: int
    pages: int
