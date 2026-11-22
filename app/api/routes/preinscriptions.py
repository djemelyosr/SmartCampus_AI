from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import candidate_user
from app.db.session import get_db
from app.models.models import PreRegistration, PreRegStatus, Program, User
from app.schemas.schemas import PreRegIn, PreRegOut

router = APIRouter(prefix="/preinscriptions", tags=["preinscriptions"])


@router.post("", response_model=PreRegOut, status_code=201)
def create(body: PreRegIn, user: User = Depends(candidate_user), db: Session = Depends(get_db)):
    program = db.get(Program, body.program_id)
    if not program or not program.active:
        raise HTTPException(404, "Program not found")
    if not (user.profile and user.profile.consent_given):
        raise HTTPException(400, "Consent required before pre-registration")
    pre = PreRegistration(user_id=user.id, program_id=body.program_id, status=PreRegStatus.submitted)
    db.add(pre)
    db.commit()
    return pre


@router.get("", response_model=list[PreRegOut])
def mine(user: User = Depends(candidate_user), db: Session = Depends(get_db)):
    return db.scalars(select(PreRegistration).where(PreRegistration.user_id == user.id)).all()
