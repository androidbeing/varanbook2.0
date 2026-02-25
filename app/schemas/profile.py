"""
schemas/profile.py – Pydantic request/response schemas for matrimonial profiles.
"""

import uuid
from datetime import date, datetime, time
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.profile import (
    Gender,
    MaritalStatus,
    ProfileStatus,
    Rashi,
    Star,
    Dhosam,
    Qualification,
    IncomeRange,
)


# ──────────────────────────────────────────────────────────────────────────────
class ProfileCreate(BaseModel):
    """Initial profile creation payload submitted by a member."""

    # ── Personal
    gender: Gender
    date_of_birth: date

    # Physical (spec: height 60-200 cm, weight 35-120 kg)
    height_cm: int | None = Field(None, ge=60, le=200)
    weight_kg: int | None = Field(None, ge=35, le=120)
    complexion: str | None = Field(None, max_length=50)
    blood_group: str | None = Field(None, pattern=r"^(A|B|AB|O)[+-]$")
    marital_status: MaritalStatus = MaritalStatus.NEVER_MARRIED
    disabilities: str | None = Field(None, max_length=500)

    # Contact
    mobile: str | None = Field(None, pattern=r"^\+[1-9]\d{6,14}$", examples=["+919876543210"])
    whatsapp: str | None = Field(None, pattern=r"^\+[1-9]\d{6,14}$", examples=["+919876543210"])

    # Location
    native_place: str | None = Field(None, max_length=100)
    current_location: str | None = Field(None, max_length=100)
    city: str | None = Field(None, max_length=100)  # backward compat
    state: str | None = Field(None, max_length=100)
    country: str = Field("India", max_length=100)

    # Religious / cultural
    religion: str | None = Field(None, max_length=100)
    caste: str | None = Field(None, max_length=100)
    sub_caste: str | None = Field(None, max_length=100)
    gotra: str | None = Field(None, max_length=100)
    mother_tongue: str | None = Field(None, max_length=100)

    # Horoscope
    time_of_birth: time | None = None
    birth_place: str | None = Field(None, max_length=200)
    rashi: Rashi | None = None
    star: Star | None = None
    dhosam: Dhosam | None = None
    nakshatra: str | None = Field(None, max_length=100)  # backward compat
    manglik: bool | None = None

    # Education / career
    qualification: Qualification | None = None
    education: str | None = Field(None, max_length=200)  # backward compat free text
    profession: str | None = Field(None, max_length=200)
    working_at: str | None = Field(None, max_length=200)
    income_range: IncomeRange | None = None
    annual_income_inr: int | None = Field(None, ge=0)  # backward compat
    occupation: str | None = Field(None, max_length=200)  # backward compat

    # Family
    father_name: str | None = Field(None, max_length=200)
    father_occupation: str | None = Field(None, max_length=200)
    mother_name: str | None = Field(None, max_length=200)
    mother_occupation: str | None = Field(None, max_length=200)
    siblings: int | None = Field(None, ge=0, le=20)
    siblings_details: str | None = Field(None, max_length=1000)

    # ── Privacy flags (default: personal visible; others hidden)
    personal_visible: bool = True
    photo_visible: bool = False
    birth_visible: bool = False
    professional_visible: bool = False
    family_visible: bool = False
    contact_visible: bool = False
    horoscope_visible: bool = False

    @field_validator("date_of_birth")
    @classmethod
    def age_must_be_18plus(cls, v: date) -> date:
        from datetime import date as _date
        age = (_date.today() - v).days // 365
        if age < 18:
            raise ValueError("Candidate must be at least 18 years old.")
        if age > 80:
            raise ValueError("Date of birth appears invalid (age > 80).")
        return v


class ProfileUpdate(ProfileCreate):
    """All fields optional for PATCH operations."""

    gender: Gender | None = None
    date_of_birth: date | None = None
    country: str | None = Field(None, max_length=100)


class ProfileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    gender: Gender
    date_of_birth: date
    height_cm: int | None
    weight_kg: int | None
    complexion: str | None
    blood_group: str | None
    marital_status: MaritalStatus
    mobile: str | None
    whatsapp: str | None
    native_place: str | None
    current_location: str | None
    city: str | None
    state: str | None
    country: str
    religion: str | None
    caste: str | None
    sub_caste: str | None
    gotra: str | None
    mother_tongue: str | None
    time_of_birth: time | None
    birth_place: str | None
    rashi: Rashi | None
    star: Star | None
    dhosam: Dhosam | None
    manglik: bool | None
    qualification: Qualification | None
    profession: str | None
    working_at: str | None
    income_range: IncomeRange | None
    annual_income_inr: int | None
    father_name: str | None
    father_occupation: str | None
    mother_name: str | None
    mother_occupation: str | None
    siblings: int | None
    siblings_details: str | None
    # Privacy flags
    personal_visible: bool
    photo_visible: bool
    birth_visible: bool
    professional_visible: bool
    family_visible: bool
    contact_visible: bool
    horoscope_visible: bool
    photo_keys: list[str] | None
    status: ProfileStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FileUploadRequest(BaseModel):
    """Request for a pre-signed S3 URL."""

    file_name: str = Field(..., max_length=255, examples=["photo.jpg"])
    content_type: str = Field(
        ...,
        pattern=r"^(image/(jpeg|png|webp|heic)|application/pdf)$",
        examples=["image/jpeg"],
    )
    upload_purpose: str = Field(
        ...,
        pattern=r"^(profile_photo|horoscope)$",
        examples=["profile_photo"],
    )


class FileUploadResponse(BaseModel):
    upload_url: str   # pre-signed PUT URL
    object_key: str   # S3 key to store in profile.photo_keys


class NotificationEnqueue(BaseModel):
    """Payload for enqueueing a push notification via SQS → Lambda → FCM."""

    user_id: uuid.UUID
    title: str = Field(..., max_length=200)
    body: str = Field(..., max_length=500)
    data: dict | None = None  # extra key/value pairs passed to FCM
