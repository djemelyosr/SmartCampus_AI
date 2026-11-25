"""Schemas of the academic catalogue (formations, spécialités, programmes pédagogiques, matières, conditions d'admission)."""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.catalog import ConditionKind, FeePeriod, PaymentMethod, PublicationStatus
from app.models.models import Institution, Level
from app.schemas.schemas import ORM

Name = Annotated[str, Field(min_length=1, max_length=255)]
OptName = Name | None


# --- Formations (programs) -------------------------------------------------------------------------------------------
class ProgramUpdate(BaseModel):
    institution: Institution | None = None
    level: Level | None = None
    name: OptName = None
    description: str | None = None
    admission_requirements: str | None = None
    duration_years: int | None = Field(default=None, ge=1, le=10)
    career_outcomes: list[str] | None = None
    active: bool | None = None


# --- Spécialités ------------------------------------------------------------------------------------------------------
class SpecialtyIn(BaseModel):
    program_id: int
    name: Name
    description: str = ""


class SpecialtyUpdate(BaseModel):
    name: OptName = None
    description: str | None = None
    active: bool | None = None


class SpecialtyOut(ORM):
    id: int
    program_id: int
    name: str
    description: str
    active: bool
    created_at: datetime


# --- Matières --------------------------------------------------------------------------------------------------------
class SubjectFields(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=32)
    semester: int | None = Field(default=None, ge=1, le=12)
    credits: int | None = Field(default=None, ge=0, le=60)
    coefficient: float | None = Field(default=None, ge=0, le=100)
    hours: int | None = Field(default=None, ge=0, le=2000)
    description: str = ""


class SubjectIn(SubjectFields):
    curriculum_id: int
    name: Name


class SubjectUpdate(BaseModel):
    curriculum_id: int | None = None
    name: OptName = None
    code: str | None = Field(default=None, min_length=1, max_length=32)
    semester: int | None = Field(default=None, ge=1, le=12)
    credits: int | None = Field(default=None, ge=0, le=60)
    coefficient: float | None = Field(default=None, ge=0, le=100)
    hours: int | None = Field(default=None, ge=0, le=2000)
    description: str | None = None
    active: bool | None = None


class SubjectOut(ORM):
    id: int
    curriculum_id: int
    code: str | None
    name: str
    semester: int | None
    credits: int | None
    coefficient: float | None
    hours: int | None
    description: str
    active: bool


# --- Programmes pédagogiques -----------------------------------------------------------------------------------------
class CurriculumIn(BaseModel):
    program_id: int
    specialty_id: int | None = None
    name: Name
    academic_year: str | None = Field(default=None, pattern=r"^\d{4}-\d{4}$")  # e.g. 2026-2027
    description: str = ""


class CurriculumUpdate(BaseModel):
    specialty_id: int | None = None
    name: OptName = None
    academic_year: str | None = Field(default=None, pattern=r"^\d{4}-\d{4}$")
    description: str | None = None
    active: bool | None = None


class CurriculumOut(ORM):
    id: int
    program_id: int
    specialty_id: int | None
    name: str
    academic_year: str | None
    description: str
    active: bool
    created_at: datetime


class CurriculumDetailOut(CurriculumOut):
    subjects: list[SubjectOut] = []


# --- Official information: publication status + validity period ---------------------------------------------------------
# Fees, payment terms and admission conditions share these fields. Candidates and the AI agent only ever see items that
# are published AND inside their validity period (empty bound = open).
def _check_period(valid_from: date | None, valid_until: date | None) -> None:
    if valid_from and valid_until and valid_until < valid_from:
        raise ValueError("valid_until must not be before valid_from")


class OfficialFields(BaseModel):
    status: PublicationStatus = PublicationStatus.draft  # `published` publishes right away; draft by default
    valid_from: date | None = None
    valid_until: date | None = None
    academic_year: str | None = Field(default=None, pattern=r"^\d{4}-\d{4}$")  # e.g. 2026-2027

    @field_validator("status")
    @classmethod
    def _not_archived(cls, v: PublicationStatus) -> PublicationStatus:
        if v == PublicationStatus.archived:
            raise ValueError("A new item cannot be created as archived")
        return v

    @model_validator(mode="after")
    def _period(self):
        _check_period(self.valid_from, self.valid_until)
        return self


class OfficialUpdate(BaseModel):
    """The status is never patched directly: it changes through /publish, /archive and /draft."""

    valid_from: date | None = None
    valid_until: date | None = None
    academic_year: str | None = Field(default=None, pattern=r"^\d{4}-\d{4}$")

    @model_validator(mode="after")
    def _period(self):
        _check_period(self.valid_from, self.valid_until)
        return self


class OfficialOut(ORM):
    status: PublicationStatus
    valid_from: date | None
    valid_until: date | None
    academic_year: str | None
    published_at: datetime | None
    official: bool  # published, active and valid today: what candidates and the agent can see


# --- Conditions d'admission ------------------------------------------------------------------------------------------
class AdmissionConditionIn(OfficialFields):
    program_id: int
    specialty_id: int | None = None  # empty = applies to the whole formation
    kind: ConditionKind = ConditionKind.other
    title: Name
    description: str = ""
    required: bool = True
    threshold: float | None = Field(default=None, ge=0)


class AdmissionConditionUpdate(OfficialUpdate):
    specialty_id: int | None = None
    kind: ConditionKind | None = None
    title: OptName = None
    description: str | None = None
    required: bool | None = None
    threshold: float | None = Field(default=None, ge=0)
    active: bool | None = None


class AdmissionConditionOut(OfficialOut):
    id: int
    program_id: int
    specialty_id: int | None
    kind: ConditionKind
    title: str
    description: str
    required: bool
    threshold: float | None
    active: bool
    created_at: datetime


# --- Frais de scolarité (tarifs) ---------------------------------------------------------------------------------------
class FeeIn(OfficialFields):
    program_id: int
    specialty_id: int | None = None  # empty = applies to the whole formation
    label: Name
    amount: float = Field(ge=0, le=1_000_000)
    currency: str = Field(default="TND", pattern=r"^[A-Z]{3}$")
    period: FeePeriod = FeePeriod.annual
    description: str = ""


class FeeUpdate(OfficialUpdate):
    specialty_id: int | None = None
    label: OptName = None
    amount: float | None = Field(default=None, ge=0, le=1_000_000)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    period: FeePeriod | None = None
    description: str | None = None
    active: bool | None = None


class FeeOut(OfficialOut):
    id: int
    program_id: int
    specialty_id: int | None
    label: str
    amount: float
    currency: str
    period: FeePeriod
    description: str
    active: bool
    created_at: datetime


# --- Modalités de paiement -----------------------------------------------------------------------------------------------
class PaymentTermIn(OfficialFields):
    program_id: int
    specialty_id: int | None = None  # empty = applies to the whole formation
    fee_id: int | None = None  # optional: the fee these terms apply to
    method: PaymentMethod = PaymentMethod.other
    title: Name
    description: str = ""
    installments: int = Field(default=1, ge=1, le=36)  # number of payments
    down_payment_percent: float | None = Field(default=None, ge=0, le=100)  # share due at registration
    due_date: date | None = None  # last day to pay (full amount or first instalment)


class PaymentTermUpdate(OfficialUpdate):
    specialty_id: int | None = None
    fee_id: int | None = None
    method: PaymentMethod | None = None
    title: OptName = None
    description: str | None = None
    installments: int | None = Field(default=None, ge=1, le=36)
    down_payment_percent: float | None = Field(default=None, ge=0, le=100)
    due_date: date | None = None
    active: bool | None = None


class PaymentTermOut(OfficialOut):
    id: int
    program_id: int
    specialty_id: int | None
    fee_id: int | None
    method: PaymentMethod
    title: str
    description: str
    installments: int
    down_payment_percent: float | None
    due_date: date | None
    active: bool
    created_at: datetime


# --- Official information of a formation (what candidates and the agent consult) ----------------------------------------
class OfficialInfoOut(BaseModel):
    program_id: int
    program_name: str
    institution: Institution
    as_of: date  # the day the validity periods were checked against
    fees: list[FeeOut]
    payment_terms: list[PaymentTermOut]
    admission_conditions: list[AdmissionConditionOut]
    complete: dict[str, bool]  # False = nothing official is published for this topic: refer to a human advisor
