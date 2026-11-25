from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.catalog import apply_update, ensure_scope, get_or_404, hide_if_inactive, manager_only, page, restrict_visibility, search
from app.api.deps import optional_user
from app.db.session import get_db
from app.models.catalog import Specialty
from app.models.models import Institution, Program, User
from app.schemas.catalog import SpecialtyIn, SpecialtyOut, SpecialtyUpdate

router = APIRouter(prefix="/specialties", tags=["specialties"])


def _name_taken(db: Session, program_id: int, name: str, except_id: int | None = None) -> bool:
    stmt = select(Specialty.id).where(Specialty.program_id == program_id, Specialty.name == name)
    if except_id is not None:
        stmt = stmt.where(Specialty.id != except_id)
    return db.scalar(stmt) is not None


@router.get("", response_model=list[SpecialtyOut])
def list_specialties(
    response: Response,
    q: str = "",
    program_id: int | None = None,
    institution: Institution | None = None,
    include_inactive: bool = False,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    stmt = select(Specialty).join(Program, Specialty.program_id == Program.id).order_by(Specialty.program_id, Specialty.name)
    stmt = restrict_visibility(stmt, user, include_inactive, [Specialty.active, Program.active], Program.institution)
    stmt = search(stmt, q, Specialty.name, Specialty.description)
    if program_id is not None:
        stmt = stmt.where(Specialty.program_id == program_id)
    if institution:
        stmt = stmt.where(Program.institution == institution)
    return page(db, stmt, response, limit, offset)


@router.get("/{specialty_id}", response_model=SpecialtyOut)
def get_specialty(specialty_id: int, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    specialty = get_or_404(db, Specialty, specialty_id, "Specialty")
    hide_if_inactive(user, specialty.program.institution, specialty.active, specialty.program.active)
    return specialty


@router.post("", response_model=SpecialtyOut, status_code=201)
def create_specialty(body: SpecialtyIn, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    program = get_or_404(db, Program, body.program_id, "Program")
    ensure_scope(user, program.institution)
    if _name_taken(db, body.program_id, body.name):
        raise HTTPException(status.HTTP_409_CONFLICT, "This formation already has a specialty with that name")
    specialty = Specialty(**body.model_dump())
    db.add(specialty)
    db.commit()
    return specialty


@router.patch("/{specialty_id}", response_model=SpecialtyOut)
def update_specialty(specialty_id: int, body: SpecialtyUpdate, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    specialty = get_or_404(db, Specialty, specialty_id, "Specialty")
    ensure_scope(user, specialty.program.institution)
    if body.name is not None and _name_taken(db, specialty.program_id, body.name, except_id=specialty.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "This formation already has a specialty with that name")
    apply_update(specialty, body)
    db.commit()
    return specialty


@router.delete("/{specialty_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_specialty(specialty_id: int, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    """Deletes the specialty with its teaching programmes (and their subjects) and its admission conditions."""
    specialty = get_or_404(db, Specialty, specialty_id, "Specialty")
    ensure_scope(user, specialty.program.institution)
    db.delete(specialty)
    db.commit()
