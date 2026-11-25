"""Academic catalogue managed by the academic heads (SmartCampus.pdf, section 3): specialties, teaching programmes
(curricula), subjects and admission conditions, all attached to a `Program` (a formation).

Fees, payment terms and admission conditions are *official information*: each has a publication status and a validity
period, and only what is published AND currently valid is shown to candidates or used by the AI agent."""

import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, and_, or_
from sqlalchemy import true as sa_true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.dates import tn_today
from app.db.base import Base
from app.models.models import Program, TimestampMixin


class ConditionKind(str, enum.Enum):
    diploma = "diploma"  # baccalauréat, licence, DUT...
    average = "average"  # minimum average / grade (see `threshold`)
    document = "document"  # file to provide
    exam = "exam"  # entrance exam / test
    language = "language"
    age = "age"
    other = "other"


class FeePeriod(str, enum.Enum):
    annual = "annual"  # per academic year
    semester = "semester"
    one_time = "one_time"  # registration, certification...


class PublicationStatus(str, enum.Enum):
    draft = "draft"  # being prepared by the academic head: never shown to candidates nor used by the agent
    published = "published"  # official: visible while its validity period is running
    archived = "archived"  # withdrawn or superseded: kept for history only


class PaymentMethod(str, enum.Enum):
    bank_transfer = "bank_transfer"
    cash = "cash"
    cheque = "cheque"
    card = "card"
    online = "online"
    other = "other"


class OfficialMixin:
    """Publication status + validity period of an item (needs `active` and a `program` relationship on the model).

    Official = active AND published AND today inside [valid_from, valid_until] (empty bound = open) AND formation active."""

    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, native_enum=False, length=16), default=PublicationStatus.draft, index=True
    )
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    academic_year: Mapped[str | None] = mapped_column(String(9))  # informative, e.g. 2026-2027
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    def in_validity(self, on: date | None = None) -> bool:
        on = on or tn_today()
        return (self.valid_from is None or self.valid_from <= on) and (self.valid_until is None or on <= self.valid_until)

    @property
    def official(self) -> bool:
        return bool(self.active and self.status == PublicationStatus.published and self.in_validity() and self.program.active)

    @classmethod
    def official_clause(cls, on: date | None = None):
        """SQL twin of `official` (the formation's own `active` flag is checked by the caller's join)."""
        on = on or tn_today()
        return and_(
            cls.active.is_(True),
            cls.status == PublicationStatus.published,
            or_(cls.valid_from.is_(None), cls.valid_from <= on),
            or_(cls.valid_until.is_(None), cls.valid_until >= on),
        )

    @classmethod
    def validity_clause(cls, state: str, on: date | None = None):
        """Staff filter on the validity period alone: current | upcoming | expired."""
        on = on or tn_today()
        if state == "upcoming":
            return and_(cls.valid_from.is_not(None), cls.valid_from > on)
        if state == "expired":
            return and_(cls.valid_until.is_not(None), cls.valid_until < on)
        return and_(or_(cls.valid_from.is_(None), cls.valid_from <= on), or_(cls.valid_until.is_(None), cls.valid_until >= on))


class Specialty(Base, TimestampMixin):
    __tablename__ = "specialties"
    __table_args__ = (UniqueConstraint("program_id", "name", name="uq_specialty_program_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa_true())
    program: Mapped[Program] = relationship(back_populates="specialties")
    curricula: Mapped[list["Curriculum"]] = relationship(back_populates="specialty", cascade="all")
    admission_conditions: Mapped[list["AdmissionCondition"]] = relationship(back_populates="specialty", cascade="all")
    fees: Mapped[list["Fee"]] = relationship(back_populates="specialty", cascade="all")
    payment_terms: Mapped[list["PaymentTerm"]] = relationship(back_populates="specialty", cascade="all")


class Curriculum(Base, TimestampMixin):
    """Programme pédagogique of a formation, optionally specific to one specialty."""

    __tablename__ = "curricula"
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)
    specialty_id: Mapped[int | None] = mapped_column(ForeignKey("specialties.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    academic_year: Mapped[str | None] = mapped_column(String(9))  # e.g. 2026-2027
    description: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa_true())
    program: Mapped[Program] = relationship(back_populates="curricula")
    specialty: Mapped[Specialty | None] = relationship(back_populates="curricula")
    subjects: Mapped[list["Subject"]] = relationship(
        back_populates="curriculum", cascade="all", order_by="(Subject.semester, Subject.name)"
    )


class Subject(Base, TimestampMixin):
    """Matière of a teaching programme."""

    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("curriculum_id", "code", name="uq_subject_curriculum_code"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    curriculum_id: Mapped[int] = mapped_column(ForeignKey("curricula.id"), index=True)
    code: Mapped[str | None] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(255))
    semester: Mapped[int | None] = mapped_column(Integer)
    credits: Mapped[int | None] = mapped_column(Integer)
    coefficient: Mapped[float | None] = mapped_column(Float)
    hours: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa_true())
    curriculum: Mapped[Curriculum] = relationship(back_populates="subjects")


class AdmissionCondition(Base, TimestampMixin, OfficialMixin):
    """Admission condition of a formation (program-wide when `specialty_id` is empty)."""

    __tablename__ = "admission_conditions"
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)
    specialty_id: Mapped[int | None] = mapped_column(ForeignKey("specialties.id"), index=True)
    kind: Mapped[ConditionKind] = mapped_column(Enum(ConditionKind), default=ConditionKind.other)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    required: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa_true())
    threshold: Mapped[float | None] = mapped_column(Float)  # e.g. minimum average
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa_true())
    program: Mapped[Program] = relationship(back_populates="admission_conditions")
    specialty: Mapped[Specialty | None] = relationship(back_populates="admission_conditions")


class Fee(Base, TimestampMixin, OfficialMixin):
    """Tarif of a formation (program-wide when `specialty_id` is empty): tuition, registration, laboratory fees..."""

    __tablename__ = "fees"
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)
    specialty_id: Mapped[int | None] = mapped_column(ForeignKey("specialties.id"), index=True)
    label: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="TND", server_default="TND")
    period: Mapped[FeePeriod] = mapped_column(Enum(FeePeriod), default=FeePeriod.annual)
    description: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa_true())
    program: Mapped[Program] = relationship(back_populates="fees")
    specialty: Mapped[Specialty | None] = relationship(back_populates="fees")


class PaymentTerm(Base, TimestampMixin, OfficialMixin):
    """Modalité de paiement of a formation (program-wide when `specialty_id` is empty): how, when and in how many
    instalments the fees are paid. Optionally tied to one `Fee` (e.g. the annual tuition)."""

    __tablename__ = "payment_terms"
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)
    specialty_id: Mapped[int | None] = mapped_column(ForeignKey("specialties.id"), index=True)
    fee_id: Mapped[int | None] = mapped_column(ForeignKey("fees.id", ondelete="SET NULL"), index=True)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod, native_enum=False, length=16), default=PaymentMethod.other)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    installments: Mapped[int] = mapped_column(Integer, default=1, server_default="1")  # number of payments
    down_payment_percent: Mapped[float | None] = mapped_column(Float)  # share due at registration
    due_date: Mapped[date | None] = mapped_column(Date)  # last day to pay (first instalment / full amount)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa_true())
    program: Mapped[Program] = relationship(back_populates="payment_terms")
    specialty: Mapped[Specialty | None] = relationship(back_populates="payment_terms")
