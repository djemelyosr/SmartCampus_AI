from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.catalog import (
    Validity, check_specialty, ensure_scope, get_or_404, hide_unless_official, manager_only, page, restrict_official, search, staff_filters,
)
from app.api.deps import optional_user
from app.api.publication import add_workflow_routes, publish, update_official
from app.db.session import get_db
from app.models.catalog import Fee, PaymentMethod, PaymentTerm, PublicationStatus, Specialty
from app.models.models import Institution, Program, User
from app.schemas.catalog import PaymentTermIn, PaymentTermOut, PaymentTermUpdate

# Modalités de paiement of a formation (or of one of its specialties): method, instalments, deadline. Official information:
# the public only reads items that are published and valid today; writes and status changes belong to the academic heads.
router = APIRouter(prefix="/payment-terms", tags=["payment-terms"])


def _check_fee(db: Session, fee_id: int | None, program_id: int) -> None:
    if fee_id is None:
        return
    fee = db.get(Fee, fee_id)
    if fee is None or fee.program_id != program_id:
        raise HTTPException(422, "Fee does not belong to this formation")


@router.get("", response_model=list[PaymentTermOut])
def list_payment_terms(
    response: Response,
    q: str = "",
    program_id: int | None = None,
    specialty_id: int | None = None,
    include_program_wide: bool = False,  # with specialty_id: also return the terms of the whole formation
    fee_id: int | None = None,
    institution: Institution | None = None,
    method: PaymentMethod | None = None,
    status_filter: PublicationStatus | None = Query(None, alias="status"),  # staff view: draft | published | archived
    validity: Validity | None = None,  # staff view: current | upcoming | expired
    include_inactive: bool = False,  # team only: drafts, archived, upcoming and expired items of their institution
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    stmt = select(PaymentTerm).join(Program, PaymentTerm.program_id == Program.id).order_by(PaymentTerm.program_id, PaymentTerm.specialty_id, PaymentTerm.id)
    stmt = restrict_official(stmt, PaymentTerm, user, include_inactive, Program.institution)
    stmt = staff_filters(stmt, PaymentTerm, status_filter, validity)
    stmt = search(stmt, q, PaymentTerm.title, PaymentTerm.description)
    if program_id is not None:
        stmt = stmt.where(PaymentTerm.program_id == program_id)
    if specialty_id is not None:
        if include_program_wide:
            parent = select(Specialty.program_id).where(Specialty.id == specialty_id).scalar_subquery()
            stmt = stmt.where(
                or_(PaymentTerm.specialty_id == specialty_id, (PaymentTerm.specialty_id.is_(None)) & (PaymentTerm.program_id == parent))
            )
        else:
            stmt = stmt.where(PaymentTerm.specialty_id == specialty_id)
    if fee_id is not None:
        stmt = stmt.where(PaymentTerm.fee_id == fee_id)
    if institution:
        stmt = stmt.where(Program.institution == institution)
    if method:
        stmt = stmt.where(PaymentTerm.method == method)
    return page(db, stmt, response, limit, offset)


@router.get("/{term_id}", response_model=PaymentTermOut)
def get_payment_term(term_id: int, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    term = get_or_404(db, PaymentTerm, term_id, "Payment term")
    hide_unless_official(user, term)
    return term


@router.post("", response_model=PaymentTermOut, status_code=201)
def create_payment_term(body: PaymentTermIn, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    program = get_or_404(db, Program, body.program_id, "Program")
    ensure_scope(user, program.institution)
    check_specialty(db, body.specialty_id, body.program_id)
    _check_fee(db, body.fee_id, body.program_id)
    term = PaymentTerm(**body.model_dump(exclude={"status"}))  # draft unless `status: published` was sent
    db.add(term)
    db.flush()
    if body.status == PublicationStatus.published:
        publish(db, term, user, "title")
    db.commit()
    return term


@router.patch("/{term_id}", response_model=PaymentTermOut)
def update_payment_term(term_id: int, body: PaymentTermUpdate, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    term = get_or_404(db, PaymentTerm, term_id, "Payment term")
    ensure_scope(user, term.program.institution)
    if "specialty_id" in body.model_fields_set:
        check_specialty(db, body.specialty_id, term.program_id)
    if "fee_id" in body.model_fields_set:
        _check_fee(db, body.fee_id, term.program_id)
    update_official(term, body, nullable=frozenset({"specialty_id", "fee_id", "down_payment_percent", "due_date"}))
    db.commit()
    return term


@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_term(term_id: int, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    term = get_or_404(db, PaymentTerm, term_id, "Payment term")
    ensure_scope(user, term.program.institution)
    db.delete(term)
    db.commit()


add_workflow_routes(router, PaymentTerm, "Payment term", PaymentTermOut, "title")
