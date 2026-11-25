from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.api.catalog import apply_update, ensure_scope, get_or_404, hide_if_inactive, manager_only, page, restrict_visibility, search
from app.api.deps import optional_user
from app.db.session import get_db
from app.models.models import DocumentChunk, Institution, Level, PreRegistration, Program, User
from app.schemas.catalog import ProgramUpdate
from app.schemas.schemas import ProgramIn, ProgramOut

# Formations. Public reading; creation / change / removal for the academic head of the institution (or the administrator).
router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("", response_model=list[ProgramOut])
def list_programs(
    response: Response,
    q: str = "",
    institution: Institution | None = None,
    level: Level | None = None,
    min_duration_years: int | None = Query(None, ge=1),
    max_duration_years: int | None = Query(None, ge=1),
    include_inactive: bool = False,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    q_ = select(Program).order_by(Program.id)
    q_ = restrict_visibility(q_, user, include_inactive, [Program.active], Program.institution)
    q_ = search(q_, q, Program.name, Program.description, Program.admission_requirements)
    if institution:
        q_ = q_.where(Program.institution == institution)
    if level:
        q_ = q_.where(Program.level == level)
    if min_duration_years is not None:
        q_ = q_.where(Program.duration_years >= min_duration_years)
    if max_duration_years is not None:
        q_ = q_.where(Program.duration_years <= max_duration_years)
    return page(db, q_, response, limit, offset)


@router.get("/{program_id}", response_model=ProgramOut)
def get_program(program_id: int, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    program = get_or_404(db, Program, program_id, "Program")
    hide_if_inactive(user, program.institution, program.active)
    return program


@router.post("", response_model=ProgramOut, status_code=201)
def create_program(body: ProgramIn, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    ensure_scope(user, body.institution)
    program = Program(**body.model_dump())
    db.add(program)
    db.commit()
    return program


@router.patch("/{program_id}", response_model=ProgramOut)
def update_program(program_id: int, body: ProgramUpdate, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    program = get_or_404(db, Program, program_id, "Program")
    ensure_scope(user, program.institution)
    if body.institution is not None:
        ensure_scope(user, body.institution)
    apply_update(program, body, nullable=frozenset({"duration_years"}))
    db.commit()
    return program


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_program(program_id: int, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    """Deletes the formation with its specialties, teaching programmes, subjects and admission conditions."""
    program = get_or_404(db, Program, program_id, "Program")
    ensure_scope(user, program.institution)
    if db.scalar(select(func.count()).select_from(PreRegistration).where(PreRegistration.program_id == program_id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Formation linked to pre-registrations: deactivate it instead (active=false)")
    if db.get_bind().dialect.name != "sqlite":  # the RAG table only exists on PostgreSQL
        db.execute(update(DocumentChunk).where(DocumentChunk.program_id == program_id).values(program_id=None))
    db.delete(program)
    db.commit()
