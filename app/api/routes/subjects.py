from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.catalog import apply_update, ensure_scope, get_or_404, hide_if_inactive, manager_only, page, restrict_visibility, search
from app.api.deps import optional_user
from app.db.session import get_db
from app.models.catalog import Curriculum, Subject
from app.models.models import Institution, Program, User
from app.schemas.catalog import SubjectIn, SubjectOut, SubjectUpdate

# Matières of a teaching programme (a subject belongs to exactly one curriculum).
router = APIRouter(prefix="/subjects", tags=["subjects"])


def _code_taken(db: Session, curriculum_id: int, code: str | None, except_id: int | None = None) -> bool:
    if not code:
        return False
    stmt = select(Subject.id).where(Subject.curriculum_id == curriculum_id, Subject.code == code)
    if except_id is not None:
        stmt = stmt.where(Subject.id != except_id)
    return db.scalar(stmt) is not None


@router.get("", response_model=list[SubjectOut])
def list_subjects(
    response: Response,
    q: str = "",
    curriculum_id: int | None = None,
    program_id: int | None = None,
    specialty_id: int | None = None,
    institution: Institution | None = None,
    semester: int | None = Query(None, ge=1, le=12),
    min_credits: int | None = Query(None, ge=0),
    max_credits: int | None = Query(None, ge=0),
    include_inactive: bool = False,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    stmt = (
        select(Subject)
        .join(Curriculum, Subject.curriculum_id == Curriculum.id)
        .join(Program, Curriculum.program_id == Program.id)
        .order_by(Subject.curriculum_id, Subject.semester, Subject.name)
    )
    stmt = restrict_visibility(stmt, user, include_inactive, [Subject.active, Curriculum.active, Program.active], Program.institution)
    stmt = search(stmt, q, Subject.name, Subject.code, Subject.description)
    if curriculum_id is not None:
        stmt = stmt.where(Subject.curriculum_id == curriculum_id)
    if program_id is not None:
        stmt = stmt.where(Curriculum.program_id == program_id)
    if specialty_id is not None:
        stmt = stmt.where(Curriculum.specialty_id == specialty_id)
    if institution:
        stmt = stmt.where(Program.institution == institution)
    if semester is not None:
        stmt = stmt.where(Subject.semester == semester)
    if min_credits is not None:
        stmt = stmt.where(Subject.credits >= min_credits)
    if max_credits is not None:
        stmt = stmt.where(Subject.credits <= max_credits)
    return page(db, stmt, response, limit, offset)


@router.get("/{subject_id}", response_model=SubjectOut)
def get_subject(subject_id: int, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    subject = get_or_404(db, Subject, subject_id, "Subject")
    curriculum = subject.curriculum
    hide_if_inactive(user, curriculum.program.institution, subject.active, curriculum.active, curriculum.program.active)
    return subject


@router.post("", response_model=SubjectOut, status_code=201)
def create_subject(body: SubjectIn, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    curriculum = get_or_404(db, Curriculum, body.curriculum_id, "Curriculum")
    ensure_scope(user, curriculum.program.institution)
    if _code_taken(db, body.curriculum_id, body.code):
        raise HTTPException(status.HTTP_409_CONFLICT, "This teaching programme already has a subject with that code")
    subject = Subject(**body.model_dump())
    db.add(subject)
    db.commit()
    return subject


@router.patch("/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: int, body: SubjectUpdate, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    subject = get_or_404(db, Subject, subject_id, "Subject")
    ensure_scope(user, subject.curriculum.program.institution)
    target_id = subject.curriculum_id
    if body.curriculum_id is not None and body.curriculum_id != subject.curriculum_id:  # move to another programme
        target = get_or_404(db, Curriculum, body.curriculum_id, "Curriculum")
        ensure_scope(user, target.program.institution)
        target_id = target.id
    code = body.code if "code" in body.model_fields_set else subject.code
    if _code_taken(db, target_id, code, except_id=subject.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "This teaching programme already has a subject with that code")
    apply_update(subject, body, nullable=frozenset({"code", "semester", "credits", "coefficient", "hours"}))
    db.commit()
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(subject_id: int, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    subject = get_or_404(db, Subject, subject_id, "Subject")
    ensure_scope(user, subject.curriculum.program.institution)
    db.delete(subject)
    db.commit()
