"""Request/response models of the academic catalogue (formations, specialties, curricula, subjects)
and of the official information (admission conditions, fees, payment terms)."""

import re
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from app.models.models import Institution, Level, PublicationStatus
from app.schemas.schemas import ORM

TUNIS = timezone(timedelta(hours=1))  # Tunisia: UTC+1, no DST


def today_tn() -> date:
    """Calendar day in Tunisia: validity periods are compared to this day (same rule as the frontend)."""
    return datetime.now(TUNIS).date()


def is_official(status: PublicationStatus | str, active: bool, valid_from: date | None, valid_until: date | None, on: date | None = None) -> bool:
    on = on or today_tn()
    return (
        PublicationStatus(status) == PublicationStatus.published
        and bool(active)
        and (valid_from is None or valid_from <= on)
        and (valid_until is None or valid_until >= on)
    )


_YEAR = re.compile(r"^(\d{4})-(\d{4})$")


def _academic_year(v: str | None) -> str | None:
    if v is None or v == "":
        return None
    m = _YEAR.match(v.strip())
    if not m or int(m.group(2)) != int(m.group(1)) + 1:
        raise ValueError("academic_year must look like 2026-2027")
    return v.strip()


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _Validity(_In):
    valid_from: date | None = None
    valid_until: date | None = None
    academic_year: str | None = None

    _year = field_validator("academic_year")(_academic_year)

    @model_validator(mode="after")
    def _period(self):
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("valid_until must not be before valid_from")
        return self


Name = Field(min_length=1, max_length=255)
Kind = Literal["diploma", "average", "document", "exam", "language", "age", "other"]
Period = Literal["annual", "semester", "one_time"]
Method = Literal["bank_transfer", "cash", "cheque", "card", "online", "other"]
Currency = Field(pattern=r"^[A-Z]{3}$")

# ----------------------------------------------------------------------------- programs (formations)


class ProgramCreate(_In):
    institution: Institution
    level: Level
    name: str = Name
    description: str = ""
    admission_requirements: str = ""
    duration_years: int | None = Field(None, ge=1, le=10)
    career_outcomes: list[str] = []
    active: bool = True


class ProgramUpdate(_In):
    institution: Institution | None = None
    level: Level | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    admission_requirements: str | None = None
    duration_years: int | None = Field(None, ge=1, le=10)
    career_outcomes: list[str] | None = None
    active: bool | None = None


class ProgramRead(ORM):
    id: int
    institution: Institution
    level: Level
    name: str
    description: str
    admission_requirements: str
    duration_years: int | None
    career_outcomes: list[str]
    active: bool


# ----------------------------------------------------------------------------- specialties


class SpecialtyCreate(_In):
    program_id: int
    name: str = Name
    description: str = ""
    active: bool = True


class SpecialtyUpdate(_In):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    active: bool | None = None


class SpecialtyRead(ORM):
    id: int
    program_id: int
    name: str
    description: str
    active: bool


# ----------------------------------------------------------------------------- curricula (teaching programmes)


class CurriculumCreate(_In):
    program_id: int
    specialty_id: int | None = None
    name: str = Name
    academic_year: str | None = None
    description: str = ""
    active: bool = True

    _year = field_validator("academic_year")(_academic_year)


class CurriculumUpdate(_In):
    specialty_id: int | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    academic_year: str | None = None
    description: str | None = None
    active: bool | None = None

    _year = field_validator("academic_year")(_academic_year)


class CurriculumRead(ORM):
    id: int
    program_id: int
    specialty_id: int | None
    name: str
    academic_year: str | None
    description: str
    active: bool


# ----------------------------------------------------------------------------- subjects


class _SubjectFields(_In):
    code: str | None = Field(None, max_length=32)
    semester: int | None = Field(None, ge=1, le=12)
    credits: float | None = Field(None, ge=0, le=60)
    coefficient: float | None = Field(None, ge=0, le=20)
    hours: float | None = Field(None, ge=0, le=2000)


class SubjectCreate(_SubjectFields):
    curriculum_id: int
    name: str = Name
    description: str = ""
    active: bool = True


class SubjectUpdate(_SubjectFields):
    curriculum_id: int | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    active: bool | None = None


class SubjectRead(ORM):
    id: int
    curriculum_id: int
    code: str | None
    name: str
    semester: int | None
    credits: float | None
    coefficient: float | None
    hours: float | None
    description: str
    active: bool


# ----------------------------------------------------------------------------- official information


class OfficialRead(ORM):
    status: PublicationStatus
    valid_from: date | None
    valid_until: date | None
    academic_year: str | None
    published_at: datetime | None
    active: bool

    @computed_field  # type: ignore[prop-decorator]
    @property
    def official(self) -> bool:
        """Visible to candidates and the AI agent right now."""
        return is_official(self.status, self.active, self.valid_from, self.valid_until)


class AdmissionConditionCreate(_Validity):
    program_id: int
    specialty_id: int | None = None
    kind: Kind
    title: str = Name
    description: str = ""
    required: bool = True
    threshold: float | None = Field(None, ge=0)
    active: bool = True


class AdmissionConditionUpdate(_Validity):
    specialty_id: int | None = None
    kind: Kind | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    required: bool | None = None
    threshold: float | None = Field(None, ge=0)
    active: bool | None = None


class AdmissionConditionRead(OfficialRead):
    id: int
    program_id: int
    specialty_id: int | None
    kind: str
    title: str
    description: str
    required: bool
    threshold: float | None


class FeeCreate(_Validity):
    program_id: int
    specialty_id: int | None = None
    label: str = Name
    amount: float = Field(ge=0)
    currency: str = Currency
    period: Period
    description: str = ""
    active: bool = True


class FeeUpdate(_Validity):
    specialty_id: int | None = None
    label: str | None = Field(None, min_length=1, max_length=255)
    amount: float | None = Field(None, ge=0)
    currency: str | None = Field(None, pattern=r"^[A-Z]{3}$")
    period: Period | None = None
    description: str | None = None
    active: bool | None = None


class FeeRead(OfficialRead):
    id: int
    program_id: int
    specialty_id: int | None
    label: str
    amount: float
    currency: str
    period: str
    description: str


class PaymentTermCreate(_Validity):
    program_id: int
    specialty_id: int | None = None
    fee_id: int | None = None
    method: Method
    title: str = Name
    description: str = ""
    installments: int = Field(1, ge=1, le=36)
    down_payment_percent: float | None = Field(None, ge=0, le=100)
    due_date: date | None = None
    active: bool = True


class PaymentTermUpdate(_Validity):
    specialty_id: int | None = None
    fee_id: int | None = None
    method: Method | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    installments: int | None = Field(None, ge=1, le=36)
    down_payment_percent: float | None = Field(None, ge=0, le=100)
    due_date: date | None = None
    active: bool | None = None


class PaymentTermRead(OfficialRead):
    id: int
    program_id: int
    specialty_id: int | None
    fee_id: int | None
    method: str
    title: str
    description: str
    installments: int
    down_payment_percent: float | None
    due_date: date | None


class OfficialInfo(BaseModel):
    program_id: int
    program_name: str
    institution: Institution
    as_of: date
    fees: list[FeeRead]
    payment_terms: list[PaymentTermRead]
    admission_conditions: list[AdmissionConditionRead]
    complete: dict[str, bool]
