"""
schemas/partner_preference.py – Pydantic schemas for partner search preferences.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.profile import Dhosam, IncomeRange, MaritalStatus, Qualification, Rashi, Star


class PartnerPreferenceUpsert(BaseModel):
    """PUT /profiles/{id}/preferences – create or replace preferences."""

    age_min: int | None = Field(None, ge=18, le=80)
    age_max: int | None = Field(None, ge=18, le=80)
    height_min_cm: int | None = Field(None, ge=60, le=200)
    height_max_cm: int | None = Field(None, ge=60, le=200)
    weight_min_kg: int | None = Field(None, ge=35, le=120)
    weight_max_kg: int | None = Field(None, ge=35, le=120)

    qualifications: list[Qualification] = Field(default_factory=list)
    income_ranges: list[IncomeRange] = Field(default_factory=list)
    marital_statuses: list[MaritalStatus] = Field(default_factory=list)

    current_locations: list[str] = Field(default_factory=list)
    native_locations: list[str] = Field(default_factory=list)
    castes: list[str] = Field(default_factory=list)
    religions: list[str] = Field(default_factory=list)

    dhosam: list[Dhosam] = Field(default_factory=list)
    rashi: list[Rashi] = Field(default_factory=list)
    star: list[Star] = Field(default_factory=list)


class PartnerPreferenceRead(PartnerPreferenceUpsert):
    """Response shape with identity fields."""

    id: uuid.UUID
    profile_id: uuid.UUID
    updated_at: datetime

    model_config = {"from_attributes": True}
