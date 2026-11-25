from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.models import PreRegistration, Program, User
from app.schemas.schemas import PreRegIn, PreRegOut

router = APIRouter(prefix="/preinscriptions", tags=["preinscriptions"])


@router.post("", response_model=PreRegOut, status_code=201)
def create(body: PreRegIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not db.get(Program, body.program_id):
        raise HTTPException(404, "Program not found")
    if not (user.profile and user.profile.consent_given):
        raise HTTPException(400, "Consent required before pre-registration")
    pre = PreRegistration(user_id=user.id, program_id=body.program_id)
    db.add(pre)
    db.commit()
    return pre


@router.get("", response_model=list[PreRegOut])
def mine(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(PreRegistration).where(PreRegistration.user_id == user.id)).all()
