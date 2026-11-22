from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.models import Institution, Level, PreRegStatus, Role


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_validator("*", mode="after")
    @classmethod
    def _utc(cls, v):
        # SQLite returns naive datetimes (stored as UTC): make the zone explicit so clients don't read them as local time.
        return v.replace(tzinfo=timezone.utc) if isinstance(v, datetime) and v.tzinfo is None else v


def _check_password(v: str) -> str:
    from app.core.config import settings

    if len(v) < settings.password_min_length:
        raise ValueError(f"password must be at least {settings.password_min_length} characters")
    if len(v) > 128:
        raise ValueError("password is too long")
    return v


class UserCreate(BaseModel):
    """Public sign-up: always creates a candidate account."""

    email: EmailStr
    password: str
    full_name: str = Field("", max_length=255)

    _pw = field_validator("password")(_check_password)


class UserOut(ORM):
    id: int
    email: str  # not re-validated on output
    full_name: str
    role: Role
    is_active: bool = True


class AdminUserCreate(UserCreate):
    role: Role


class AdminUserUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = None

    @field_validator("password")
    @classmethod
    def _pw(cls, v: str | None) -> str | None:
        return None if v is None else _check_password(v)


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
