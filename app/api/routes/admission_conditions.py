from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.catalog import (
    Validity, check_specialty, ensure_scope, get_or_404, hide_unless_official, manager_only, page, restrict_official, search, staff_filters,
)
from app.api.deps import optional_user
from app.api.publication import add_workflow_routes, publish, update_official
from app.db.session import get_db
from app.models.catalog import AdmissionCondition, ConditionKind, PublicationStatus, Specialty
from app.models.models import Institution, Program, User
from app.schemas.catalog import AdmissionConditionIn, AdmissionConditionOut, AdmissionConditionUpdate

# Admission conditions of a formation (or of one of its specialties). Official information: the public only reads items
# that are published and valid today; writes and status changes are limited to the academic heads.
router = APIRouter(prefix="/admission-conditions", tags=["admission-conditions"])


@router.get("", response_model=list[AdmissionConditionOut])
def list_conditions(
    response: Response,
    q: str = "",
    program_id: int | None = None,
    specialty_id: int | None = None,
    include_program_wide: bool = False,  # with specialty_id: also return the conditions of the whole formation
    institution: Institution | None = None,
    kind: ConditionKind | None = None,
    required: bool | None = None,
    status_filter: PublicationStatus | None = Query(None, alias="status"),  # staff view: draft | published | archived
    validity: Validity | None = None,  # staff view: current | upcoming | expired
    include_inactive: bool = False,  # team only: drafts, archived, upcoming and expired items of their institution
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    stmt = (
        select(AdmissionCondition)
        .join(Program, AdmissionCondition.program_id == Program.id)
        .order_by(AdmissionCondition.program_id, AdmissionCondition.specialty_id, AdmissionCondition.id)
    )
    stmt = restrict_official(stmt, AdmissionCondition, user, include_inactive, Program.institution)
    stmt = staff_filters(stmt, AdmissionCondition, status_filter, validity)
    stmt = search(stmt, q, AdmissionCondition.title, AdmissionCondition.description)
    if program_id is not None:
        stmt = stmt.where(AdmissionCondition.program_id == program_id)
    if specialty_id is not None:
        if include_program_wide:
            parent = select(Specialty.program_id).where(Specialty.id == specialty_id).scalar_subquery()
            stmt = stmt.where(
                or_(
                    AdmissionCondition.specialty_id == specialty_id,
                    (AdmissionCondition.specialty_id.is_(None)) & (AdmissionCondition.program_id == parent),
                )
            )
        else:
            stmt = stmt.where(AdmissionCondition.specialty_id == specialty_id)
    if institution:
        stmt = stmt.where(Program.institution == institution)
    if kind:
        stmt = stmt.where(AdmissionCondition.kind == kind)
    if required is not None:
        stmt = stmt.where(AdmissionCondition.required.is_(required))
    return page(db, stmt, response, limit, offset)


@router.get("/{condition_id}", response_model=AdmissionConditionOut)
def get_condition(condition_id: int, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    condition = get_or_404(db, AdmissionCondition, condition_id, "Admission condition")
    hide_unless_official(user, condition)
    return condition


@router.post("", response_model=AdmissionConditionOut, status_code=201)
def create_condition(body: AdmissionConditionIn, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    program = get_or_404(db, Program, body.program_id, "Program")
    ensure_scope(user, program.institution)
    check_specialty(db, body.specialty_id, body.program_id)
    condition = AdmissionCondition(**body.model_dump(exclude={"status"}))  # draft unless `status: published` was sent
    db.add(condition)
    db.flush()
    if body.status == PublicationStatus.published:
        publish(db, condition, user, "title")
    db.commit()
    return condition


@router.patch("/{condition_id}", response_model=AdmissionConditionOut)
def update_condition(condition_id: int, body: AdmissionConditionUpdate, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    condition = get_or_404(db, AdmissionCondition, condition_id, "Admission condition")
    ensure_scope(user, condition.program.institution)
    if "specialty_id" in body.model_fields_set:
        check_specialty(db, body.specialty_id, condition.program_id)
    update_official(condition, body, nullable=frozenset({"specialty_id", "threshold"}))  # changed + published -> draft again
    db.commit()
    return condition


@router.delete("/{condition_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_condition(condition_id: int, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    condition = get_or_404(db, AdmissionCondition, condition_id, "Admission condition")
    ensure_scope(user, condition.program.institution)
    db.delete(condition)
    db.commit()


add_workflow_routes(router, AdmissionCondition, "Admission condition", AdmissionConditionOut, "title")
