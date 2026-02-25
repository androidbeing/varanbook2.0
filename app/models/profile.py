"""
models/profile.py – Matrimonial profile ORM model.

One-to-one with User. Contains all biodata fields relevant for a
matrimonial information centre – religion, caste, horoscope, etc.
"""

import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MaritalStatus(str, enum.Enum):
    NEVER_MARRIED = "never_married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    AWAITING_DIVORCE = "awaiting_divorce"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ProfileStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    MATCHED = "matched"


# 12 Vedic rashi (zodiac signs)
class Rashi(str, enum.Enum):
    MESHA = "mesha"
    VRISHABHA = "vrishabha"
    MITHUNA = "mithuna"
    KARKA = "karka"
    SIMHA = "simha"
    KANYA = "kanya"
    TULA = "tula"
    VRISHCHIKA = "vrishchika"
    DHANU = "dhanu"
    MAKARA = "makara"
    KUMBHA = "kumbha"
    MEENA = "meena"


# 27 Vedic nakshatras (lunar mansions)
class Star(str, enum.Enum):
    ASHWINI = "ashwini"
    BHARANI = "bharani"
    KRITTIKA = "krittika"
    ROHINI = "rohini"
    MRIGASHIRA = "mrigashira"
    ARDRA = "ardra"
    PUNARVASU = "punarvasu"
    PUSHYA = "pushya"
    ASHLESHA = "ashlesha"
    MAGHA = "magha"
    PURVA_PHALGUNI = "purva_phalguni"
    UTTARA_PHALGUNI = "uttara_phalguni"
    HASTA = "hasta"
    CHITRA = "chitra"
    SWATI = "swati"
    VISHAKHA = "vishakha"
    ANURADHA = "anuradha"
    JYESHTHA = "jyeshtha"
    MOOLA = "moola"
    PURVA_ASHADHA = "purva_ashadha"
    UTTARA_ASHADHA = "uttara_ashadha"
    SHRAVANA = "shravana"
    DHANISHTHA = "dhanishtha"
    SHATABHISHA = "shatabhisha"
    PURVA_BHADRAPADA = "purva_bhadrapada"
    UTTARA_BHADRAPADA = "uttara_bhadrapada"
    REVATI = "revati"


class Dhosam(str, enum.Enum):
    NONE = "none"
    CHEVVAI = "chevvai"         # Mangal dosha
    RAHU = "rahu"
    KETHU = "kethu"
    SHANI = "shani"
    MULTIPLE = "multiple"


class Qualification(str, enum.Enum):
    BELOW_10TH = "below_10th"
    SSLC = "sslc"
    HSC = "hsc"
    DIPLOMA = "diploma"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"
    PROFESSIONAL = "professional"   # CA, CS, ICWA, etc.
    OTHER = "other"


class IncomeRange(str, enum.Enum):
    BELOW_2L = "below_2l"
    TWO_TO_5L = "2_to_5l"
    FIVE_TO_10L = "5_to_10l"
    TEN_TO_20L = "10_to_20l"
    TWENTY_TO_50L = "20_to_50l"
    ABOVE_50L = "above_50l"


class Profile(Base):
    """
    Matrimonial biodata profile.

    RLS is enforced at the user level; the profile inherits isolation
    because it JOIN-walks through users.tenant_id.
    """

    __tablename__ = "profiles"

    # ── PK / FK ───────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    # Denormalised for faster RLS checks without a join
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Personal ──────────────────────────────────────────────────────────────
    gender: Mapped[Gender] = mapped_column(Enum(Gender, values_callable=lambda x: [e.value for e in x], create_type=False), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    # time_of_birth in 24h format HH:MM
    time_of_birth: Mapped[time | None] = mapped_column(Time, nullable=True)
    # height in cm; spec: 60–200
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # weight in kg; spec: 35–120
    weight_kg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    complexion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    blood_group: Mapped[str | None] = mapped_column(String(10), nullable=True)
    marital_status: Mapped[MaritalStatus] = mapped_column(
        Enum(MaritalStatus, values_callable=lambda x: [e.value for e in x], create_type=False), default=MaritalStatus.NEVER_MARRIED
    )
    disabilities: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Religious / cultural ──────────────────────────────────────────────────
    religion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    caste: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sub_caste: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gotra: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mother_tongue: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Horoscope (Birth Details) ─────────────────────────────────────────────
    birth_place: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Stored as VARCHAR; Pydantic enum validates allowed values at API layer.
    rashi: Mapped[Rashi | None] = mapped_column(String(50), nullable=True)
    star: Mapped[Star | None] = mapped_column(String(50), nullable=True)
    dhosam: Mapped[Dhosam | None] = mapped_column(String(50), nullable=True, comment="Astrological dosha/dhosam")
    manglik: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # ── Professional ─────────────────────────────────────────────────────────
    # Stored as VARCHAR; Pydantic enum validates allowed values at API layer.
    qualification: Mapped[Qualification | None] = mapped_column(String(50), nullable=True)
    profession: Mapped[str | None] = mapped_column(String(200), nullable=True)
    working_at: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Employer / organisation name"
    )
    income_range: Mapped[IncomeRange | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India")
    native_place: Mapped[str | None] = mapped_column(String(200), nullable=True)
    current_location: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # ── Family ────────────────────────────────────────────────────────────────
    father_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    father_occupation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mother_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mother_occupation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    siblings_details: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Free-text sibling info (count, married status, etc.)"
    )

    # ── Contact ───────────────────────────────────────────────────────────────
    mobile: Mapped[str | None] = mapped_column(String(20), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── Media (up to 10 photos + 1 horoscope) ────────────────────────────────
    # S3 object keys; actual metadata stored in file_records table
    photo_keys: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True, comment="S3 object keys for photos (max 10)"
    )
    horoscope_key: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="S3 object key for horoscope PDF/image"
    )

    # ── Privacy flags (default: only personal section is visible) ─────────────
    # Each flag = True means that section is visible to other members.
    personal_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    photo_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    birth_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    professional_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    family_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    contact_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    horoscope_visible: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Status ────────────────────────────────────────────────────────────────
    status: Mapped[ProfileStatus] = mapped_column(
        Enum(ProfileStatus, values_callable=lambda x: [e.value for e in x], create_type=False), default=ProfileStatus.DRAFT
    )

    # ── Audit ─────────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="profile")  # noqa: F821
    partner_preference: Mapped["PartnerPreference | None"] = relationship(  # noqa: F821
        "PartnerPreference", back_populates="profile",
        uselist=False, cascade="all, delete-orphan",
    )
    shortlists_sent: Mapped[list["Shortlist"]] = relationship(  # noqa: F821
        "Shortlist", foreign_keys="Shortlist.from_profile_id",
        back_populates="from_profile", cascade="all, delete-orphan",
    )
    shortlists_received: Mapped[list["Shortlist"]] = relationship(  # noqa: F821
        "Shortlist", foreign_keys="Shortlist.to_profile_id",
        back_populates="to_profile",
    )

    def __repr__(self) -> str:
        return f"<Profile user_id={self.user_id} status={self.status}>"
