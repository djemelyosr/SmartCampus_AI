import enum
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
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


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.candidate)
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


class DocumentChunk(Base):
    """RAG corpus chunk (official IIT/ISB sources)."""

    __tablename__ = "document_chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(512))
    institution: Mapped[Institution | None] = mapped_column(Enum(Institution))
    program_id: Mapped[int | None] = mapped_column(ForeignKey("programs.id"))
    content: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(settings.embedding_dim))


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    language: Mapped[str | None] = mapped_column(String(16))  # fr | tn | arabizi
    state: Mapped[dict] = mapped_column(JSON, default=dict)  # agent memory / graph state
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", order_by="Message.id")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant | tool
    content: Mapped[str] = mapped_column(Text)
    modality: Mapped[str] = mapped_column(String(8), default="text")  # text | audio
    audio_path: Mapped[str | None] = mapped_column(String(512))
    meta: Mapped[dict] = mapped_column(JSON, default=dict)  # sources, intent, language...
    conversation: Mapped[Conversation] = relationship(back_populates="messages")


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
