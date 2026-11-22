from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import candidate_user
from app.db.session import get_db
from app.models.models import Appointment, PreRegistration, PreRegStatus, User

router = APIRouter(prefix="/appointments", tags=["appointments"])

TUNIS = timezone(timedelta(hours=1))  # Tunisia: UTC+1, no DST
SLOT_TIMES = [time(9, 0), time(10, 0), time(11, 30), time(14, 0)]
SLOT_MINUTES = 30
ACTIVE = ("proposed", "confirmed")


class BookIn(BaseModel):
    slot: datetime  # ISO 8601, timezone-aware recommended (naive = Tunis time)


class AppointmentOut(BaseModel):
    id: int
    scheduled_at: datetime
    ends_at: datetime
    status: str
    mode: str = "Visioconférence"


def _utc(dt: datetime) -> datetime:
    return (dt if dt.tzinfo else dt.replace(tzinfo=TUNIS)).astimezone(timezone.utc)


def _db_utc(dt: datetime) -> datetime:
    """Values read from the DB: aware on PostgreSQL, naive (already UTC) on SQLite."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _out(a: Appointment) -> AppointmentOut:
    start = _db_utc(a.scheduled_at)
    return AppointmentOut(id=a.id, scheduled_at=start, ends_at=start + timedelta(minutes=SLOT_MINUTES), status=a.status)


def _taken(db: Session) -> set[datetime]:
    rows = db.scalars(select(Appointment).where(Appointment.status.in_(ACTIVE))).all()
    return {_db_utc(r.scheduled_at) for r in rows}


@router.get("/slots")
def slots(start: date | None = None, days: int = 7, user: User = Depends(candidate_user), db: Session = Depends(get_db)):
    """Bookable 30-min slots on weekdays (Mon-Fri), Tunis time, excluding past and taken slots."""
    days = max(1, min(days, 21))
    first = start or datetime.now(TUNIS).date()
    taken, now, out = _taken(db), datetime.now(timezone.utc), []
    for d in range(days):
        day = first + timedelta(days=d)
        if day.weekday() >= 5:
            continue
        for t in SLOT_TIMES:
            at = datetime.combine(day, t, tzinfo=TUNIS)
            out.append({"slot": at.isoformat(), "available": at.astimezone(timezone.utc) > now and at.astimezone(timezone.utc) not in taken})
    return out


@router.get("/me", response_model=list[AppointmentOut])
def mine(user: User = Depends(candidate_user), db: Session = Depends(get_db)):
    pre_ids = db.scalars(select(PreRegistration.id).where(PreRegistration.user_id == user.id)).all()
    if not pre_ids:
        return []
    rows = db.scalars(select(Appointment).where(Appointment.pre_registration_id.in_(pre_ids)).order_by(Appointment.id.desc())).all()
    return [_out(a) for a in rows]


@router.post("", response_model=AppointmentOut, status_code=201)
def book(body: BookIn, user: User = Depends(candidate_user), db: Session = Depends(get_db)):
    pre = db.scalars(select(PreRegistration).where(PreRegistration.user_id == user.id).order_by(PreRegistration.id.desc())).first()
    if not pre:
        raise HTTPException(409, "Une pré-inscription est nécessaire avant de réserver un entretien")
    at = _utc(body.slot)
    local = at.astimezone(TUNIS)
    if local.weekday() >= 5 or local.time() not in SLOT_TIMES or local.second or local.microsecond:
        raise HTTPException(422, "Créneau invalide")
    if at <= datetime.now(timezone.utc):
        raise HTTPException(422, "Ce créneau est passé")
    if at in _taken(db):
        raise HTTPException(409, "Ce créneau n’est plus disponible")
    existing = db.scalars(select(Appointment).where(Appointment.pre_registration_id == pre.id, Appointment.status.in_(ACTIVE))).first()
    if existing:
        raise HTTPException(409, "Un rendez-vous est déjà réservé : annulez-le avant d’en choisir un autre")
    a = Appointment(pre_registration_id=pre.id, scheduled_at=at, status="confirmed")
    db.add(a)
    pre.status = PreRegStatus.interview_scheduled
    db.commit()
    return _out(a)


@router.delete("/{appointment_id}", response_model=AppointmentOut)
def cancel(appointment_id: int, user: User = Depends(candidate_user), db: Session = Depends(get_db)):
    a = db.get(Appointment, appointment_id)
    pre = db.get(PreRegistration, a.pre_registration_id) if a else None
    if not a or not pre or pre.user_id != user.id:
        raise HTTPException(404, "Rendez-vous introuvable")
    if a.status not in ACTIVE:
        raise HTTPException(409, "Rendez-vous déjà annulé")
    a.status = "cancelled"
    pre.status = PreRegStatus.qcm_pending
    db.commit()
    return _out(a)
