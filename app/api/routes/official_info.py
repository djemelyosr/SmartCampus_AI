from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.catalog import check_specialty, get_or_404, hide_if_inactive
from app.api.deps import optional_user
from app.db.session import get_db
from app.models.models import Program, User
from app.schemas.catalog import OfficialInfoOut
from app.services.official_info import official_info

router = APIRouter(prefix="/programs", tags=["official-info"])


@router.get("/{program_id}/official-info", response_model=OfficialInfoOut)
def get_official_info(
    program_id: int,
    specialty_id: int | None = None,  # with a specialty: the whole formation + this specialty
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    """Everything a candidate (or the AI agent) may rely on for a formation: published and currently valid fees, payment
    terms and admission conditions, in one call. Same answer for everyone, team accounts included: drafts and expired
    items are managed through the individual resources. `complete` tells which topics have nothing official yet."""
    program = get_or_404(db, Program, program_id, "Program")
    hide_if_inactive(user, program.institution, program.active)
    if specialty_id is not None:
        check_specialty(db, specialty_id, program_id)
    info = official_info(db, program, specialty_id)
    return OfficialInfoOut(
        program_id=program.id,
        program_name=program.name,
        institution=program.institution,
        as_of=info["as_of"],
        fees=info["fees"],
        payment_terms=info["payment_terms"],
        admission_conditions=info["admission_conditions"],
        complete=info["complete"],
    )
