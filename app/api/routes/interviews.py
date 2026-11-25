"""Interview preparation for the interviewer (and academic heads, limited to their institution)."""

from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.orientation import LABELS
from app.api.deps import require_roles
from app.db.session import get_db
from app.models.models import Appointment, Conversation, PreRegistration, Program, Qcm, Role, User
from app.services import qcm as qcm_service

router = APIRouter(prefix="/interviews", tags=["interviews"])
TEAM = (Role.interviewer, Role.iit_head, Role.isb_head)


def _scope(user: User) -> str | None:
    return {Role.iit_head: "IIT", Role.isb_head: "ISB"}.get(user.role)


def _qcm_result(db: Session, pre_id: int) -> dict | None:
    q = db.scalars(select(Qcm).where(Qcm.pre_registration_id == pre_id)).first()
    if not q or q.score is None:
        return None
    return qcm_service.score({int(k): v for k, v in (q.answers or {}).items()}, q.questions)


def _appointment(db: Session, pre_id: int) -> dict | None:
    a = db.scalars(select(Appointment).where(Appointment.pre_registration_id == pre_id, Appointment.status.in_(("proposed", "confirmed")))).first()
    if not a:
        return None
    at = a.scheduled_at if a.scheduled_at.tzinfo else a.scheduled_at.replace(tzinfo=timezone.utc)
    return {"id": a.id, "scheduled_at": at.isoformat(), "status": a.status}


def _item(db: Session, pre: PreRegistration, user: User, prog: Program) -> dict:
    res = _qcm_result(db, pre.id)
    return {
        "id": pre.id, "reference": f"SC-{pre.created_at.year if pre.created_at else 2026}-{pre.id:04d}",
        "name": user.full_name or user.email, "program": prog.name, "institution": prog.institution.value, "status": pre.status.value,
        "qcm": {"good": res["good"], "total": res["total"]} if res else None, "appointment": _appointment(db, pre.id),
    }


@router.get("/candidates")
def candidates(user: User = Depends(require_roles(*TEAM)), db: Session = Depends(get_db)):
    scope, out = _scope(user), []
    for pre in db.scalars(select(PreRegistration).order_by(PreRegistration.id.desc())).all():
        prog, cand = db.get(Program, pre.program_id), db.get(User, pre.user_id)
        if prog and cand and (scope is None or prog.institution.value == scope):
            out.append(_item(db, pre, cand, prog))
    return out


def _summary(name: str, profile: dict, prof_row) -> str:
    lab = lambda keys: ", ".join(LABELS.get(k, k) for k in keys)  # noqa: E731
    parts = [f"{name.split()[0] if name else 'Le candidat'}"]
    if profile.get("subjects"):
        parts.append(f"aime {lab(profile['subjects'])}")
    if profile.get("interests"):
        parts.append(f"s’intéresse à {lab(profile['interests'])}")
    if profile.get("tracks"):
        parts.append(f"envisage {lab(profile['tracks'])}")
    if profile.get("style"):
        parts.append(f"préfère une approche : {lab(profile['style'])}")
    level = (prof_row.school_level if prof_row else None) or profile.get("level")
    if level:
        parts.append(f"niveau déclaré : {level}")
    return (", ".join(parts) + ".") if len(parts) > 1 else "Peu d’informations recueillies dans la conversation : explorer le profil à l’oral."


@router.get("/candidates/{pre_id}")
def candidate(pre_id: int, user: User = Depends(require_roles(*TEAM)), db: Session = Depends(get_db)):
    pre = db.get(PreRegistration, pre_id)
    prog = db.get(Program, pre.program_id) if pre else None
    cand = db.get(User, pre.user_id) if pre else None
    if not pre or not prog or not cand or (_scope(user) and prog.institution.value != _scope(user)):
        raise HTTPException(404, "Dossier introuvable")
    conv = db.scalars(select(Conversation).where(Conversation.user_id == cand.id).order_by(Conversation.id.desc())).first()
    profile = ((conv.state or {}).get("profile") if conv else None) or {}
    row = cand.profile
    res = _qcm_result(db, pre.id)
    shortlist = [p.name for p in (db.get(Program, i) for i in profile.get("shortlist", [])) if p]
    return {
        **_item(db, pre, cand, prog),
        "language": conv.language if conv else None,
        "summary": _summary(cand.full_name or "", profile, row),
        "school_level": row.school_level if row else None,
        "career_goal": row.career_goal if row else None,
        "recommendation": {"chosen": prog.name, "shortlist": shortlist, "validated_by_human": False},
        "qcm_result": res,
        "points": qcm_service.interview_points(res, row, prog.name),
        "disclaimer": "Synthèse IA à relire · Aucune décision d’admission : validation humaine obligatoire.",
    }
