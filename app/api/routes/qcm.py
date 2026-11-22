from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import candidate_user
from app.db.session import get_db
from app.models.models import PreRegistration, PreRegStatus, Qcm, User
from app.services import qcm as qcm_service

router = APIRouter(prefix="/qcm", tags=["qcm"])


class AnswersIn(BaseModel):
    answers: dict[int, int]  # question index -> chosen option index
    finish: bool = False


def _latest_prereg(db: Session, user: User) -> PreRegistration:
    pre = db.scalars(
        select(PreRegistration).where(PreRegistration.user_id == user.id).order_by(PreRegistration.id.desc())
    ).first()
    if not pre:
        raise HTTPException(409, "Une pré-inscription est nécessaire avant le QCM")
    return pre


def _own(db: Session, qcm_id: int, user: User) -> Qcm:
    qcm = db.get(Qcm, qcm_id)
    pre = db.get(PreRegistration, qcm.pre_registration_id) if qcm else None
    if not qcm or not pre or pre.user_id != user.id:
        raise HTTPException(404, "QCM introuvable")
    return qcm


def _view(qcm: Qcm) -> dict:
    return {
        "id": qcm.id,
        "questions": qcm.questions,
        "answers": {int(k): v for k, v in (qcm.answers or {}).items()},
        "finished": qcm.score is not None,
    }


@router.get("/current")
def current(user: User = Depends(candidate_user), db: Session = Depends(get_db)):
    """Return (creating it if needed) the QCM of the candidate's latest pre-registration."""
    pre = _latest_prereg(db, user)
    qcm = db.scalars(select(Qcm).where(Qcm.pre_registration_id == pre.id)).first()
    if not qcm:
        qcm = Qcm(pre_registration_id=pre.id, questions=qcm_service.public_questions(), answers={})
        db.add(qcm)
        if pre.status in (PreRegStatus.draft, PreRegStatus.submitted):
            pre.status = PreRegStatus.qcm_pending
        db.commit()
    return _view(qcm)


@router.put("/{qcm_id}/answers")
def save_answers(qcm_id: int, body: AnswersIn, user: User = Depends(candidate_user), db: Session = Depends(get_db)):
    qcm = _own(db, qcm_id, user)
    if qcm.score is not None:
        raise HTTPException(409, "QCM déjà terminé")
    n = len(qcm.questions)
    for i, choice in body.answers.items():
        if not 0 <= i < n or not 0 <= choice < len(qcm.questions[i]["options"]):
            raise HTTPException(422, f"Réponse invalide pour la question {i}")
    qcm.answers = {str(i): c for i, c in body.answers.items()}
    if body.finish:
        if len(qcm.answers) < n:
            raise HTTPException(422, "Toutes les questions doivent être répondues")
        res = qcm_service.score({int(k): v for k, v in qcm.answers.items()})
        qcm.score = res["good"]
        qcm.summary = res["summary"]
        qcm.finished_at = datetime.now(timezone.utc)
    db.commit()
    return _view(qcm)


@router.get("/{qcm_id}/results")
def results(qcm_id: int, user: User = Depends(candidate_user), db: Session = Depends(get_db)):
    qcm = _own(db, qcm_id, user)
    if qcm.score is None:
        raise HTTPException(409, "Le QCM n’est pas terminé")
    res = qcm_service.score({int(k): v for k, v in qcm.answers.items()})
    fin = qcm.finished_at  # naive (UTC) on SQLite, aware on PostgreSQL
    res["finished_at"] = (fin if fin.tzinfo else fin.replace(tzinfo=timezone.utc)).isoformat() if fin else None
    res["disclaimer"] = "Score illustratif · Aucun seuil officiel d’admission · Décision humaine uniquement."
    return res
