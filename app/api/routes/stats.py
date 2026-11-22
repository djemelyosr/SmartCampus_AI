"""Aggregated statistics (screens 22 and "Statistiques"): counts only, no identifiable candidate except the
short list of files awaiting an action. Academic heads only ever see their own institution."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import institution_scope, require_roles
from app.db.session import get_db
from app.models.models import Appointment, Conversation, Institution, Message, PreRegistration, PreRegStatus, Program, Role, User

router = APIRouter(prefix="/stats", tags=["stats"])

PENDING = (PreRegStatus.submitted, PreRegStatus.qcm_pending, PreRegStatus.interview_scheduled, PreRegStatus.validated)
STEP = {
    PreRegStatus.submitted: ("Pré-inscription reçue", "Examiner le dossier"),
    PreRegStatus.qcm_pending: ("QCM en cours", "Suivre le QCM"),
    PreRegStatus.interview_scheduled: ("Entretien planifié", "Préparer l’entretien"),
    PreRegStatus.validated: ("Orientation validée", "Confirmer l’inscription"),
}


def _prereg_q(inst: Institution | None):
    q = select(PreRegistration).join(Program, PreRegistration.program_id == Program.id)
    return q.where(Program.institution == inst) if inst else q


def _conversation_ids(db: Session, inst: Institution | None) -> list[int]:
    q = select(Conversation.id)
    if inst:  # conversations of candidates who applied to this institution
        users = select(PreRegistration.user_id).join(Program, PreRegistration.program_id == Program.id).where(Program.institution == inst)
        q = q.where(Conversation.user_id.in_(users))
    return list(db.scalars(q).all())


def _totals(db: Session, inst: Institution | None) -> dict:
    conv_ids = _conversation_ids(db, inst)
    oriented = (
        db.scalar(select(func.count(func.distinct(Message.conversation_id))).where(Message.conversation_id.in_(conv_ids), Message.role == "assistant"))
        if conv_ids
        else 0
    )
    preregs = db.scalars(_prereg_q(inst)).all()
    pre_ids = [p.id for p in preregs]
    interviews = (
        db.scalar(select(func.count()).select_from(Appointment).where(Appointment.pre_registration_id.in_(pre_ids), Appointment.status.in_(("confirmed", "done"))))
        if pre_ids
        else 0
    )
    submitted = sum(1 for p in preregs if p.status != PreRegStatus.draft)
    enrolled = sum(1 for p in preregs if p.status == PreRegStatus.enrolled)
    conversations = len(conv_ids)
    return {
        "conversations": conversations,
        "orientations": oriented or 0,
        "preinscriptions": submitted,
        "interviews": interviews or 0,
        "enrollments": enrolled,
        "pending": sum(1 for p in preregs if p.status in PENDING),
        "conversion": round(100 * enrolled / conversations, 1) if conversations else 0.0,
    }


@router.get("/overview")
def overview(
    institution: Institution | None = None,
    user: User = Depends(require_roles(Role.direction, Role.iit_head, Role.isb_head)),
    db: Session = Depends(get_db),
):
    own = institution_scope(user)
    if own and institution and institution != own:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Statistics of another institution are not available")
    inst = own or institution

    totals = _totals(db, inst)
    funnel = [
        {"label": "Conversations", "value": totals["conversations"]},
        {"label": "Orientations", "value": totals["orientations"]},
        {"label": "Pré-inscrits", "value": totals["preinscriptions"]},
        {"label": "Entretiens", "value": totals["interviews"]},
        {"label": "Inscriptions", "value": totals["enrollments"]},
    ]

    programs = []
    prog_q = select(Program).where(Program.institution == inst) if inst else select(Program)
    for p in db.scalars(prog_q.order_by(Program.institution, Program.name)).all():
        rows = db.scalars(select(PreRegistration).where(PreRegistration.program_id == p.id)).all()
        programs.append({
            "institution": p.institution.value,
            "name": p.name,
            "orientations": len(rows),
            "preinscriptions": sum(1 for r in rows if r.status != PreRegStatus.draft),
            "validated": sum(1 for r in rows if r.status in (PreRegStatus.validated, PreRegStatus.enrolled)),
            "interest": len(rows),
        })
    programs.sort(key=lambda r: (-r["interest"], r["name"]))

    pending = []
    for pre in db.scalars(_prereg_q(inst).where(PreRegistration.status.in_(PENDING)).order_by(PreRegistration.created_at.desc(), PreRegistration.id.desc()).limit(10)).all():
        cand = db.get(User, pre.user_id)
        prog = db.get(Program, pre.program_id)
        step, action = STEP[pre.status]
        pending.append({"candidate": (cand.full_name or cand.email) if cand else "—", "institution": prog.institution.value if prog else None, "step": step, "action": action})

    conv_ids = _conversation_ids(db, inst)
    metas = db.scalars(select(Message.meta).where(Message.conversation_id.in_(conv_ids), Message.role == "assistant")).all() if conv_ids else []
    sourced = sum(1 for m in metas if isinstance(m, dict) and m.get("sources"))
    agents = {
        "messages": len(metas),
        "handoffs": sum(1 for m in metas if isinstance(m, dict) and m.get("handoff")),
        "sourced_pct": round(100 * sourced / len(metas), 1) if metas else None,
    }

    out = {"scope": inst.value if inst else "all", "totals": totals, "funnel": funnel, "programs": programs, "pending": pending, "agents": agents}
    if inst is None:
        out["by_institution"] = {i.value: _totals(db, i) for i in Institution}
    return out
