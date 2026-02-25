"""
schemas/shortlist.py – Pydantic schemas for the shortlist / accept flow.

States:
  shortlisted → accepted | rejected
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.shortlist import ShortlistStatus


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
