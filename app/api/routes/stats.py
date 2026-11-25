"""Aggregated statistics for Direction (global) and academic heads (own institution only). No candidate is identifiable
in the aggregates; the `pending` list only exists for the funnel follow-up and is limited to first name + step."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.models import Appointment, Conversation, Message, PreRegistration, PreRegStatus, Program, Qcm, Role, User

router = APIRouter(prefix="/stats", tags=["stats"])

PENDING = (PreRegStatus.draft, PreRegStatus.submitted, PreRegStatus.qcm_pending)
INTERVIEWED = (PreRegStatus.interview_scheduled, PreRegStatus.validated, PreRegStatus.enrolled)
SOURCED_ACTIONS = ("shortlist", "compare", "no_source_handoff")


def _pct(a: int, b: int) -> float:
    return round(100 * a / b, 1) if b else 0.0


def _shortlist(conv: Conversation) -> list[int]:
    return list(((conv.state or {}).get("profile") or {}).get("shortlist") or [])


@router.get("/overview")
def overview(institution: str | None = None, user: User = Depends(require_roles(Role.direction, Role.iit_head, Role.isb_head)), db: Session = Depends(get_db)):
    # Academic heads only ever see their own institution, whatever the query says.
    if user.role == Role.iit_head:
        institution = "IIT"
    elif user.role == Role.isb_head:
        institution = "ISB"
    institution = institution if institution in ("IIT", "ISB") else None

    progs = {p.id: p for p in db.scalars(select(Program).where(Program.active.is_(True))).all()}
    inst_of = lambda pid: progs[pid].institution.value if pid in progs else None  # noqa: E731
    convs = db.scalars(select(Conversation)).all()
    pres = db.scalars(select(PreRegistration)).all()
    booked = {a.pre_registration_id for a in db.scalars(select(Appointment).where(Appointment.status.in_(("proposed", "confirmed")))).all()}
    qcm_done = {q.pre_registration_id for q in db.scalars(select(Qcm)).all() if q.score is not None}
    users = {u.id: u for u in db.scalars(select(User)).all()}

    def block(inst: str | None) -> dict:
        cv = [c for c in convs if inst is None or any(inst_of(i) == inst for i in _shortlist(c))]
        pr = [p for p in pres if inst is None or inst_of(p.program_id) == inst]
        orient = [c for c in cv if _shortlist(c)]
        interviews = [p for p in pr if p.id in booked or p.status in INTERVIEWED]
        enrolled = [p for p in pr if p.status == PreRegStatus.enrolled]
        return {
            "conversations": len(cv), "orientations": len(orient), "preinscriptions": len(pr),
            "interviews": len(interviews), "enrollments": len(enrolled),
            "pending": len([p for p in pr if p.status in PENDING]),
            "conversion": _pct(len(enrolled), len(cv)),
        }

    scope = block(institution)
    programs = []
    for p in progs.values():
        if institution and p.institution.value != institution:
            continue
        shortlisted = {c.user_id for c in convs if p.id in _shortlist(c)}
        mine = [r for r in pres if r.program_id == p.id]
        programs.append({
            "institution": p.institution.value, "name": p.name, "orientations": len(shortlisted),
            "preinscriptions": len(mine), "validated": len([r for r in mine if r.status in (PreRegStatus.validated, PreRegStatus.enrolled)]),
            "interest": len(shortlisted | {r.user_id for r in mine}),
        })
    programs.sort(key=lambda r: r["interest"], reverse=True)

    pending = []
    for r in pres:
        if r.status not in PENDING or (institution and inst_of(r.program_id) != institution):
            continue
        step, action = ("QCM à terminer", "Relancer pour le QCM") if r.status == PreRegStatus.qcm_pending and r.id not in qcm_done else \
            ("Entretien à planifier", "Proposer un entretien") if r.id in qcm_done and r.id not in booked else ("Pré-inscription", "Examiner le dossier")
        name = (users[r.user_id].full_name or "Candidat").split()[0] if r.user_id in users else "Candidat"
        pending.append({"candidate": name, "institution": inst_of(r.program_id), "step": step, "action": action})

    msgs = db.scalars(select(Message).where(Message.role == "assistant")).all()
    sourcable = [m for m in msgs if str((m.meta or {}).get("action", "")).startswith("rag_") or (m.meta or {}).get("action") in SOURCED_ACTIONS]
    sourced = [m for m in sourcable if (m.meta or {}).get("sources")]
    out = {
        "scope": institution or "IIT & ISB",
        "totals": scope,
        "funnel": [
            {"label": "Conversations", "value": scope["conversations"]}, {"label": "Orientations", "value": scope["orientations"]},
            {"label": "Pré-inscrits", "value": scope["preinscriptions"]}, {"label": "Entretiens", "value": scope["interviews"]},
            {"label": "Inscriptions", "value": scope["enrollments"]},
        ],
        "programs": programs,
        "pending": pending[:20],
        "agents": {
            "handoffs": len([m for m in msgs if (m.meta or {}).get("handoff")]),
            "sourced_pct": round(100 * len(sourced) / len(sourcable)) if sourcable else None,
            "messages": len(msgs),
        },
    }
    if institution is None:
        out["by_institution"] = {"IIT": block("IIT"), "ISB": block("ISB")}
    return out
