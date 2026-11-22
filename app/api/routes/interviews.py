"""Candidates ready for an interview (screen 21): synthesis, profile, QCM and appointment.
Interviewers see every file; academic heads only their institution's; the administrator everything."""

from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import institution_scope, require_roles
from app.db.session import get_db
from app.models.models import Appointment, Conversation, Document, PreRegistration, PreRegStatus, Program, Qcm, Role, User
from app.services import qcm as qcm_service

router = APIRouter(prefix="/interviews", tags=["interviews"])
team = require_roles(Role.interviewer, Role.iit_head, Role.isb_head)

READY = (PreRegStatus.qcm_pending, PreRegStatus.interview_scheduled, PreRegStatus.validated)
ACTIVE_APPT = ("proposed", "confirmed")
DISCLAIMER = "Synthèse et scores indicatifs, à vérifier pendant l’entretien. La décision d’admission reste humaine."


def _utc(dt):
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _ref(pre: PreRegistration) -> str:
    return f"SC-{(pre.created_at.year if pre.created_at else 2026)}-{pre.id:04d}"


def _finished_qcm(db: Session, pre: PreRegistration) -> Qcm | None:
    return db.scalars(select(Qcm).where(Qcm.pre_registration_id == pre.id, Qcm.score.is_not(None)).order_by(Qcm.id.desc())).first()


def _appointment(db: Session, pre: PreRegistration) -> Appointment | None:
    return db.scalars(select(Appointment).where(Appointment.pre_registration_id == pre.id, Appointment.status.in_(ACTIVE_APPT)).order_by(Appointment.id.desc())).first()


def _item(db: Session, pre: PreRegistration) -> dict:
    user, prog = db.get(User, pre.user_id), db.get(Program, pre.program_id)
    q, a = _finished_qcm(db, pre), _appointment(db, pre)
    return {
        "id": pre.id,
        "reference": _ref(pre),
        "name": (user.full_name or user.email) if user else "—",
        "program": prog.name if prog else "—",
        "institution": prog.institution.value if prog else "",
        "status": pre.status.value,
        "qcm": {"good": q.score, "total": len(q.questions)} if q else None,
        "appointment": {"id": a.id, "scheduled_at": _utc(a.scheduled_at), "status": a.status} if a else None,
    }


def _ready(db: Session, user: User):
    q = select(PreRegistration).join(Program, PreRegistration.program_id == Program.id).where(PreRegistration.status.in_(READY))
    own = institution_scope(user)
    if own:
        q = q.where(Program.institution == own)
    return [p for p in db.scalars(q.order_by(PreRegistration.id)).all() if _finished_qcm(db, p) or _appointment(db, p)]


@router.get("/candidates")
def candidates(user: User = Depends(team), db: Session = Depends(get_db)):
    items = [_item(db, p) for p in _ready(db, user)]
    items.sort(key=lambda i: (i["appointment"] is None, i["appointment"]["scheduled_at"] if i["appointment"] else 0, i["id"]))
    return items


@router.get("/candidates/{pre_id}")
def candidate(pre_id: int, user: User = Depends(team), db: Session = Depends(get_db)):
    pre = db.get(PreRegistration, pre_id)
    prog = db.get(Program, pre.program_id) if pre else None
    own = institution_scope(user)
    if not pre or not prog or (own and prog.institution != own):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate file not found")
    cand = db.get(User, pre.user_id)
    profile = cand.profile if cand else None
    conv = db.scalars(select(Conversation).where(Conversation.user_id == pre.user_id).order_by(Conversation.id.desc())).first()

    q = _finished_qcm(db, pre)
    qcm_result = None
    if q:
        res = qcm_service.score({int(k): v for k, v in (q.answers or {}).items()})
        qcm_result = {
            "good": res["good"], "total": res["total"], "pct": res["pct"],
            "by_section": [{k: s[k] for k in ("section", "good", "total", "pct")} for s in res["by_section"]],
        }

    interests = ", ".join((profile.favorite_subjects or []) + (profile.interests or [])) if profile else ""
    goal = profile.career_goal if profile else None
    summary = " ".join(filter(None, [
        f"Intérêts déclarés : {interests}." if interests else "",
        f"Projet : {goal}." if goal else "",
        f"Formation choisie : {prog.name} ({prog.institution.value}).",
        f"{len(conv.messages)} message(s) échangé(s) avec l’assistant." if conv else "Aucune conversation enregistrée.",
    ]))

    points = []
    if qcm_result:
        weakest = sorted(qcm_result["by_section"], key=lambda s: s["pct"])[:2]
        points += [f"Revenir sur « {s['section']} » ({s['good']}/{s['total']})." for s in weakest if s["pct"] < 100]
    constraints = (profile.constraints or {}) if profile else {}
    if not constraints.get("mobilite") and not constraints.get("city"):
        points.append("Confirmer la mobilité et la ville de résidence.")
    if not constraints.get("budget"):
        points.append("Aborder le budget et les modalités de paiement.")
    if not db.scalar(select(Document.id).where(Document.user_id == pre.user_id, Document.kind == "Relevé de notes")):
        points.append("Demander ou vérifier le relevé de notes (non déposé).")
    points.append("Explorer la motivation et un exemple de projet personnel.")

    others = db.scalars(select(Program.name).join(PreRegistration, PreRegistration.program_id == Program.id).where(PreRegistration.user_id == pre.user_id, Program.id != prog.id)).all()
    return {
        **_item(db, pre),
        "language": conv.language if conv else None,
        "summary": summary,
        "school_level": profile.school_level if profile else None,
        "career_goal": goal,
        "recommendation": {
            "chosen": prog.name,
            "shortlist": [prog.name, *others],
            "validated_by_human": pre.status in (PreRegStatus.validated, PreRegStatus.enrolled),
        },
        "qcm_result": qcm_result,
        "points": points,
        "disclaimer": DISCLAIMER,
    }
