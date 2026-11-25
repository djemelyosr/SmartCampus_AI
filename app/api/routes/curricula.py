from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.catalog import (
    apply_update, check_specialty, ensure_scope, get_or_404, hide_if_inactive, is_staff, manager_only, page, restrict_visibility, scope_of, search,
)
from app.api.deps import optional_user
from app.db.session import get_db
from app.models.catalog import Curriculum
from app.models.models import Institution, Program, User
from app.schemas.catalog import CurriculumDetailOut, CurriculumIn, CurriculumOut, CurriculumUpdate

# Programmes pédagogiques of a formation (optionally of one specialty); their subjects live under /subjects.
router = APIRouter(prefix="/curricula", tags=["curricula"])


@router.get("", response_model=list[CurriculumOut])
def list_curricula(
    response: Response,
    q: str = "",
    program_id: int | None = None,
    specialty_id: int | None = None,
    institution: Institution | None = None,
    academic_year: str | None = None,
    include_inactive: bool = False,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    stmt = select(Curriculum).join(Program, Curriculum.program_id == Program.id).order_by(Curriculum.program_id, Curriculum.name)
    stmt = restrict_visibility(stmt, user, include_inactive, [Curriculum.active, Program.active], Program.institution)
    stmt = search(stmt, q, Curriculum.name, Curriculum.description)
    if program_id is not None:
        stmt = stmt.where(Curriculum.program_id == program_id)
    if specialty_id is not None:
        stmt = stmt.where(Curriculum.specialty_id == specialty_id)
    if institution:
        stmt = stmt.where(Program.institution == institution)
    if academic_year:
        stmt = stmt.where(Curriculum.academic_year == academic_year)
    return page(db, stmt, response, limit, offset)


@router.get("/{curriculum_id}", response_model=CurriculumDetailOut)
def get_curriculum(curriculum_id: int, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    """The programme with its subjects (inactive subjects are only returned to the managers of the institution)."""
    curriculum = get_or_404(db, Curriculum, curriculum_id, "Curriculum")
    institution = curriculum.program.institution
    hide_if_inactive(user, institution, curriculum.active, curriculum.program.active)
    scope = scope_of(user) if user else None
    sees_all = is_staff(user) and (scope is None or scope == institution)
    out = CurriculumDetailOut.model_validate(curriculum)
    out.subjects = [s for s in out.subjects if s.active or sees_all]
    return out


@router.post("", response_model=CurriculumOut, status_code=201)
def create_curriculum(body: CurriculumIn, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    program = get_or_404(db, Program, body.program_id, "Program")
    ensure_scope(user, program.institution)
    check_specialty(db, body.specialty_id, body.program_id)
    curriculum = Curriculum(**body.model_dump())
    db.add(curriculum)
    db.commit()
    return curriculum


@router.patch("/{curriculum_id}", response_model=CurriculumOut)
def update_curriculum(curriculum_id: int, body: CurriculumUpdate, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    curriculum = get_or_404(db, Curriculum, curriculum_id, "Curriculum")
    ensure_scope(user, curriculum.program.institution)
    if "specialty_id" in body.model_fields_set:
        check_specialty(db, body.specialty_id, curriculum.program_id)
    apply_update(curriculum, body, nullable=frozenset({"specialty_id", "academic_year"}))
    db.commit()
    return curriculum


@router.delete("/{curriculum_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_curriculum(curriculum_id: int, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    """Deletes the teaching programme with all its subjects."""
    curriculum = get_or_404(db, Curriculum, curriculum_id, "Curriculum")
    ensure_scope(user, curriculum.program.institution)
    db.delete(curriculum)
    db.commit()
