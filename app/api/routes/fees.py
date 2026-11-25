from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.catalog import (
    Validity, check_specialty, ensure_scope, get_or_404, hide_unless_official, manager_only, page, restrict_official, search, staff_filters,
)
from app.api.deps import optional_user
from app.api.publication import add_workflow_routes, publish, update_official
from app.db.session import get_db
from app.models.catalog import Fee, FeePeriod, PublicationStatus, Specialty
from app.models.models import Institution, Program, User
from app.schemas.catalog import FeeIn, FeeOut, FeeUpdate

# Frais de scolarité of a formation (or of one of its specialties). Official information: the public only reads items that
# are published and valid today; writes and status changes are limited to the academic heads.
router = APIRouter(prefix="/fees", tags=["fees"])


@router.get("", response_model=list[FeeOut])
def list_fees(
    response: Response,
    q: str = "",
    program_id: int | None = None,
    specialty_id: int | None = None,
    include_program_wide: bool = False,  # with specialty_id: also return the fees of the whole formation
    institution: Institution | None = None,
    period: FeePeriod | None = None,
    status_filter: PublicationStatus | None = Query(None, alias="status"),  # staff view: draft | published | archived
    validity: Validity | None = None,  # staff view: current | upcoming | expired
    include_inactive: bool = False,  # team only: drafts, archived, upcoming and expired items of their institution
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    stmt = select(Fee).join(Program, Fee.program_id == Program.id).order_by(Fee.program_id, Fee.specialty_id, Fee.id)
    stmt = restrict_official(stmt, Fee, user, include_inactive, Program.institution)
    stmt = staff_filters(stmt, Fee, status_filter, validity)
    stmt = search(stmt, q, Fee.label, Fee.description)
    if program_id is not None:
        stmt = stmt.where(Fee.program_id == program_id)
    if specialty_id is not None:
        if include_program_wide:
            parent = select(Specialty.program_id).where(Specialty.id == specialty_id).scalar_subquery()
            stmt = stmt.where(or_(Fee.specialty_id == specialty_id, (Fee.specialty_id.is_(None)) & (Fee.program_id == parent)))
        else:
            stmt = stmt.where(Fee.specialty_id == specialty_id)
    if institution:
        stmt = stmt.where(Program.institution == institution)
    if period:
        stmt = stmt.where(Fee.period == period)
    return page(db, stmt, response, limit, offset)


@router.get("/{fee_id}", response_model=FeeOut)
def get_fee(fee_id: int, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    fee = get_or_404(db, Fee, fee_id, "Fee")
    hide_unless_official(user, fee)
    return fee


@router.post("", response_model=FeeOut, status_code=201)
def create_fee(body: FeeIn, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    program = get_or_404(db, Program, body.program_id, "Program")
    ensure_scope(user, program.institution)
    check_specialty(db, body.specialty_id, body.program_id)
    fee = Fee(**body.model_dump(exclude={"status"}))  # created as draft unless `status: published` was sent
    db.add(fee)
    db.flush()
    if body.status == PublicationStatus.published:
        publish(db, fee, user, "label")
    db.commit()
    return fee


@router.patch("/{fee_id}", response_model=FeeOut)
def update_fee(fee_id: int, body: FeeUpdate, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    fee = get_or_404(db, Fee, fee_id, "Fee")
    ensure_scope(user, fee.program.institution)
    if "specialty_id" in body.model_fields_set:
        check_specialty(db, body.specialty_id, fee.program_id)
    update_official(fee, body, nullable=frozenset({"specialty_id"}))  # a changed published fee goes back to draft
    db.commit()
    return fee


@router.delete("/{fee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fee(fee_id: int, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    fee = get_or_404(db, Fee, fee_id, "Fee")
    ensure_scope(user, fee.program.institution)
    db.delete(fee)
    db.commit()


add_workflow_routes(router, Fee, "Fee", FeeOut, "label")  # POST /{id}/publish, /{id}/archive, /{id}/draft
