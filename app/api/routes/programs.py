from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.models import Institution, Level, Program, Role
from app.schemas.schemas import ProgramIn, ProgramOut

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("", response_model=list[ProgramOut])
def list_programs(
    institution: Institution | None = None,
    level: Level | None = None,
    db: Session = Depends(get_db),
):
    q = select(Program).where(Program.active.is_(True))
    if institution:
        q = q.where(Program.institution == institution)
    if level:
        q = q.where(Program.level == level)
    return db.scalars(q).all()


@router.get("/{program_id}", response_model=ProgramOut)
def get_program(program_id: int, db: Session = Depends(get_db)):
    program = db.get(Program, program_id)
    if not program:
        raise HTTPException(404, "Program not found")
    return program


@router.post("", response_model=ProgramOut, status_code=201,
             dependencies=[Depends(require_roles(Role.iit_head, Role.isb_head))])
def create_program(body: ProgramIn, db: Session = Depends(get_db)):
    program = Program(**body.model_dump())
    db.add(program)
    db.commit()
    return program
