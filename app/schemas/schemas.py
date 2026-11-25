from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.models import ApprovalStatus, Institution, Level, PreRegStatus, Role

# Roles a visitor may ask for when signing up. A team role is granted by an administrator; the platform
# administrator role is never self-service (it is created by an existing administrator or by the seed).
SELF_REGISTER_ROLES = (Role.candidate, Role.iit_head, Role.isb_head, Role.interviewer, Role.direction)


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_validator("*", mode="after")
    @classmethod
    def _utc(cls, v):
        # SQLite returns naive datetimes (stored as UTC): make the zone explicit so clients don't read them as local time.
        return v.replace(tzinfo=timezone.utc) if isinstance(v, datetime) and v.tzinfo is None else v


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)
    full_name: str = ""
    role: Role = Role.candidate  # a team role stays pending until an administrator approves it

    @field_validator("role")
    @classmethod
    def _self_service_role(cls, v: Role) -> Role:
        if v not in SELF_REGISTER_ROLES:
            raise ValueError("This role cannot be requested at sign-up")
        return v


class UserOut(ORM):
    id: int
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool = True
    approval_status: ApprovalStatus = ApprovalStatus.approved
    requested_role: Role | None = None  # the role asked for at sign-up (pending / rejected requests)
    reviewed_at: datetime | None = None
    review_note: str | None = None
    is_blocked: bool = False
    blocked_reason: str | None = None
    blocked_at: datetime | None = None


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)
    full_name: str = ""
    role: Role = Role.candidate


class AdminUserUpdate(BaseModel):
    full_name: str | None = None
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=12)


class AccountStatusUpdate(BaseModel):
    """Administrator's choice of account state: active, inactive (reactivable) or blocked (with a reason)."""

    status: Literal["active", "inactive", "blocked"]
    reason: str | None = Field(default=None, max_length=500)  # kept for a block


class AccessApproval(BaseModel):
    """Administrator's decision on an access request."""

    role: Role | None = None  # approve with another role than the requested one
    note: str | None = Field(default=None, max_length=500)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileIn(BaseModel):
    phone: str | None = None
    school_level: str | None = None
    favorite_subjects: list[str] = []
    interests: list[str] = []
    career_goal: str | None = None
    constraints: dict = {}
    consent_given: bool = False


class ProfileOut(ProfileIn, ORM):
    id: int
    user_id: int


class ProgramIn(BaseModel):
    institution: Institution
    level: Level
    name: str
    description: str = ""
    admission_requirements: str = ""
    duration_years: int | None = None
    career_outcomes: list[str] = []


class ProgramOut(ProgramIn, ORM):
    id: int
    active: bool


class MessageIn(BaseModel):
    content: str
    modality: str = "text"


class MessageOut(ORM):
    id: int
    role: str
    content: str
    modality: str
    meta: dict
    created_at: datetime


class ConversationOut(ORM):
    id: int
    language: str | None
    created_at: datetime
    messages: list[MessageOut] = []


class PreRegIn(BaseModel):
    program_id: int


class PreRegOut(ORM):
    id: int
    user_id: int
    program_id: int
    status: PreRegStatus
    compatibility_score: int | None
    summary: str | None
