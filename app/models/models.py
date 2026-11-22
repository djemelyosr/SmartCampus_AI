import enum
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base


class Role(str, enum.Enum):
    candidate = "candidate"
    iit_head = "iit_head"
    isb_head = "isb_head"
    interviewer = "interviewer"
    direction = "direction"
    admin = "admin"


class Institution(str, enum.Enum):
    IIT = "IIT"
    ISB = "ISB"


class Level(str, enum.Enum):
    licence = "licence"
    prepa = "prepa"
    ingenierie = "ingenierie"
    other = "other"


class PreRegStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    qcm_pending = "qcm_pending"
    interview_scheduled = "interview_scheduled"
    validated = "validated"
    enrolled = "enrolled"
    abandoned = "abandoned"


class PublicationStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class GuestStatus(str, enum.Enum):
    active = "active"
    claimed = "claimed"  # attached to a candidate account
    expired = "expired"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --------------------------------------------------------------------------- accounts


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.candidate)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    profile: Mapped["CandidateProfile | None"] = relationship(back_populates="user", uselist=False)


class CandidateProfile(Base, TimestampMixin):
    __tablename__ = "candidate_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    phone: Mapped[str | None] = mapped_column(String(32))
    school_level: Mapped[str | None] = mapped_column(String(64))
    favorite_subjects: Mapped[list] = mapped_column(JSON, default=list)
    interests: Mapped[list] = mapped_column(JSON, default=list)
    career_goal: Mapped[str | None] = mapped_column(Text)
    constraints: Mapped[dict] = mapped_column(JSON, default=dict)
    consent_given: Mapped[bool] = mapped_column(default=False)
    user: Mapped[User] = relationship(back_populates="profile")


# --------------------------------------------------------------------------- academic catalogue


class Program(Base):
    __tablename__ = "programs"
    id: Mapped[int] = mapped_column(primary_key=True)
    institution: Mapped[Institution] = mapped_column(Enum(Institution))
    level: Mapped[Level] = mapped_column(Enum(Level))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    admission_requirements: Mapped[str] = mapped_column(Text, default="")
    duration_years: Mapped[int | None] = mapped_column(Integer)
    career_outcomes: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(default=True)


class Specialty(Base):
    __tablename__ = "specialties"
    __table_args__ = (UniqueConstraint("program_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(default=True)


class Curriculum(Base):
    """Teaching programme of a formation (optionally of one specialty), for an academic year."""

    __tablename__ = "curricula"
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)
    specialty_id: Mapped[int | None] = mapped_column(ForeignKey("specialties.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    academic_year: Mapped[str | None] = mapped_column(String(9))  # 2026-2027
    description: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(default=True)


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("curriculum_id", "code"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    curriculum_id: Mapped[int] = mapped_column(ForeignKey("curricula.id"), index=True)
    code: Mapped[str | None] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(255))
    semester: Mapped[int | None] = mapped_column(Integer)
    credits: Mapped[float | None] = mapped_column(Float)
    coefficient: Mapped[float | None] = mapped_column(Float)
    hours: Mapped[float | None] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(default=True)


class OfficialMixin:
    """Official information: only `published`, `active` AND valid today is shown to candidates and the AI agent."""

    status: Mapped[PublicationStatus] = mapped_column(Enum(PublicationStatus), default=PublicationStatus.draft)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    academic_year: Mapped[str | None] = mapped_column(String(9))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active: Mapped[bool] = mapped_column(default=True)


class AdmissionCondition(Base, OfficialMixin):
    __tablename__ = "admission_conditions"
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)
    specialty_id: Mapped[int | None] = mapped_column(ForeignKey("specialties.id"))
    kind: Mapped[str] = mapped_column(String(16))  # diploma | average | document | exam | language | age | other
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    required: Mapped[bool] = mapped_column(default=True)
    threshold: Mapped[float | None] = mapped_column(Float)


class Fee(Base, OfficialMixin):
    __tablename__ = "fees"
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)
    specialty_id: Mapped[int | None] = mapped_column(ForeignKey("specialties.id"))
    label: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="TND")
    period: Mapped[str] = mapped_column(String(16))  # annual | semester | one_time
    description: Mapped[str] = mapped_column(Text, default="")


class PaymentTerm(Base, OfficialMixin):
    __tablename__ = "payment_terms"
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)
    specialty_id: Mapped[int | None] = mapped_column(ForeignKey("specialties.id"))
    fee_id: Mapped[int | None] = mapped_column(ForeignKey("fees.id"))
    method: Mapped[str] = mapped_column(String(16))  # bank_transfer | cash | cheque | card | online | other
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    installments: Mapped[int] = mapped_column(Integer, default=1)
    down_payment_percent: Mapped[float | None] = mapped_column(Float)
    due_date: Mapped[date | None] = mapped_column(Date)


class DocumentChunk(Base):
    """RAG corpus chunk (official IIT/ISB sources). PostgreSQL + pgvector only."""

    __tablename__ = "document_chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(512))
    institution: Mapped[Institution | None] = mapped_column(Enum(Institution))
    program_id: Mapped[int | None] = mapped_column(ForeignKey("programs.id"))
    content: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(settings.embedding_dim))


# --------------------------------------------------------------------------- conversations


class GuestSession(Base, TimestampMixin):
    """Temporary visitor session, created when a visitor starts chatting without an account.

    The client holds a secret token `<id>.<secret>`; only a SHA-256 hash of the secret is stored, so a database
    leak does not expose usable tokens. Holding the token is the proof that the session belongs to someone.
    """

    __tablename__ = "guest_sessions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # public identifier (uuid4 hex)
    secret_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[GuestStatus] = mapped_column(Enum(GuestStatus), default=GuestStatus.active, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    client_hash: Mapped[str | None] = mapped_column(String(64), index=True)  # salted hash of the IP, for rate limits
    language: Mapped[str | None] = mapped_column(String(16))
    claimed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    claim_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    # Exactly one owner: a candidate account, or a visitor session until it is claimed.
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    guest_session_id: Mapped[str | None] = mapped_column(ForeignKey("guest_sessions.id"), index=True)
    language: Mapped[str | None] = mapped_column(String(16))  # fr | tn | arabizi
    state: Mapped[dict] = mapped_column(JSON, default=dict)  # agent memory / graph state
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", order_by="Message.id", cascade="all, delete-orphan")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant | tool
    content: Mapped[str] = mapped_column(Text)
    modality: Mapped[str] = mapped_column(String(8), default="text")  # text | audio
    audio_path: Mapped[str | None] = mapped_column(String(512))
    meta: Mapped[dict] = mapped_column(JSON, default=dict)  # sources, intent, language, handoff...
    conversation: Mapped[Conversation] = relationship(back_populates="messages")


# --------------------------------------------------------------------------- application journey


class PreRegistration(Base, TimestampMixin):
    __tablename__ = "pre_registrations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"))
    status: Mapped[PreRegStatus] = mapped_column(Enum(PreRegStatus), default=PreRegStatus.draft)
    compatibility_score: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[str | None] = mapped_column(Text)


class Qcm(Base, TimestampMixin):
    __tablename__ = "qcms"
    id: Mapped[int] = mapped_column(primary_key=True)
    pre_registration_id: Mapped[int] = mapped_column(ForeignKey("pre_registrations.id"), index=True)
    questions: Mapped[list] = mapped_column(JSON, default=list)
    answers: Mapped[list] = mapped_column(JSON, default=list)
    score: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[str | None] = mapped_column(Text)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(primary_key=True)
    pre_registration_id: Mapped[int] = mapped_column(ForeignKey("pre_registrations.id"), index=True)
    interviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="proposed")
    notes: Mapped[str | None] = mapped_column(Text)


class Document(Base, TimestampMixin):
    """Candidate-uploaded file (transcript, ID...). Never used as RAG source."""

    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(64), default="Relevé de notes")
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), default="a_verifier")  # a_verifier | conforme | refuse
