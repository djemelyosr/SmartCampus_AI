"""Academic catalogue and official information (formations, specialties, curricula, subjects,
admission conditions, fees, payment terms).

Who sees what
- Visitors and candidates: active items of active formations only; official information (conditions, fees,
  payment terms) only when PUBLISHED, active AND valid today (Tunisia calendar day).
- Team accounts: everything when `include_inactive=true` (drafts, archived, inactive).

Who changes what
- An academic head changes only their own institution (IIT head -> IIT, ISB head -> ISB); the administrator
  changes everything. Every other role is read-only.
- Changing the content of a PUBLISHED official item sends it back to draft: it must be republished.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import Select, delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import can_edit_institution, current_user, is_staff, optional_user
from app.db.session import get_db
from app.models.models import (
    AdmissionCondition,
    Curriculum,
    Fee,
    Institution,
    Level,
    PaymentTerm,
    PreRegistration,
    Program,
    PublicationStatus,
    Specialty,
    Subject,
    User,
)
from app.schemas import catalog as S
from app.schemas.catalog import today_tn

router = APIRouter(tags=["catalogue"])


@dataclass
class Resource:
    path: str
    model: Any
    create: type[BaseModel]
    update: type[BaseModel]
    read: type[BaseModel]
    search: tuple[str, ...]
    official: bool = False
    title_attr: str | None = None  # same title + same formation/specialty = same official item (overlap check)
    order: tuple[str, ...] = ("id",)
    filters: tuple[str, ...] = field(default_factory=tuple)


RESOURCES = {
    r.path: r
    for r in [
        Resource("programs", Program, S.ProgramCreate, S.ProgramUpdate, S.ProgramRead, ("name", "description"), order=("institution", "name"), filters=("level",)),
        Resource("specialties", Specialty, S.SpecialtyCreate, S.SpecialtyUpdate, S.SpecialtyRead, ("name", "description"), order=("program_id", "name")),
        Resource("curricula", Curriculum, S.CurriculumCreate, S.CurriculumUpdate, S.CurriculumRead, ("name", "description", "academic_year"), order=("program_id", "name"), filters=("specialty_id",)),
        Resource("subjects", Subject, S.SubjectCreate, S.SubjectUpdate, S.SubjectRead, ("name", "code", "description"), order=("curriculum_id", "semester", "name"), filters=("curriculum_id", "semester")),
        Resource("admission-conditions", AdmissionCondition, S.AdmissionConditionCreate, S.AdmissionConditionUpdate, S.AdmissionConditionRead, ("title", "description"), official=True, title_attr="title", filters=("kind", "specialty_id")),
        Resource("fees", Fee, S.FeeCreate, S.FeeUpdate, S.FeeRead, ("label", "description"), official=True, title_attr="label", filters=("specialty_id",)),
        Resource("payment-terms", PaymentTerm, S.PaymentTermCreate, S.PaymentTermUpdate, S.PaymentTermRead, ("title", "description"), official=True, title_attr="title", filters=("specialty_id",)),
    ]
}

FORBIDDEN = "Only the academic head of this institution (or an administrator) can change it"


# ----------------------------------------------------------------------------- helpers


def _program_join(res: Resource, q: Select) -> Select:
    """Join the owning formation so we can filter by institution / formation and hide inactive formations."""
    m = res.model
    if m is Program:
        return q
    if m is Subject:
        return q.join(Curriculum, Subject.curriculum_id == Curriculum.id).join(Program, Curriculum.program_id == Program.id)
    return q.join(Program, m.program_id == Program.id)


def _program_of(db: Session, res: Resource, obj: Any) -> Program | None:
    if res.model is Program:
        return obj
    if res.model is Subject:
        cur = db.get(Curriculum, obj.curriculum_id)
        return db.get(Program, cur.program_id) if cur else None
    return db.get(Program, obj.program_id)


def _official_now(m: Any) -> list:
    t = today_tn()
    return [
        m.status == PublicationStatus.published,
        m.active.is_(True),
        or_(m.valid_from.is_(None), m.valid_from <= t),
        or_(m.valid_until.is_(None), m.valid_until >= t),
    ]


def _visible(res: Resource, q: Select, user: User | None, include_inactive: bool) -> Select:
    m = res.model
    if is_staff(user) and include_inactive:
        return q
    q = q.where(Program.active.is_(True))
    if m is not Program:
        q = q.where(m.active.is_(True))
    if m is Subject:
        q = q.where(Curriculum.active.is_(True))
    if res.official and not is_staff(user):
        q = q.where(*_official_now(m))
    return q


def _get(db: Session, res: Resource, item_id: int, user: User | None, include_inactive: bool = True) -> Any:
    q = _visible(res, _program_join(res, select(res.model)).where(res.model.id == item_id), user, include_inactive)
    obj = db.scalar(q)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{res.path} item not found")
    return obj


def _check_refs(db: Session, res: Resource, obj: Any) -> None:
    """Parents exist and are consistent (a specialty / fee must belong to the same formation)."""
    m = res.model
    if m is Subject:
        if not db.get(Curriculum, obj.curriculum_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "curriculum not found")
        return
    if m is Program:
        return
    if not db.get(Program, obj.program_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "programme not found")
    sid = getattr(obj, "specialty_id", None)
    if sid is not None:
        sp = db.get(Specialty, sid)
        if not sp or sp.program_id != obj.program_id:
            raise HTTPException(422, "specialty does not belong to this programme")
    fid = getattr(obj, "fee_id", None)
    if fid is not None:
        fee = db.get(Fee, fid)
        if not fee or fee.program_id != obj.program_id:
            raise HTTPException(422, "fee does not belong to this programme")
    if res.official and obj.valid_from and obj.valid_until and obj.valid_until < obj.valid_from:
        raise HTTPException(422, "valid_until must not be before valid_from")


def _check_unique(db: Session, res: Resource, obj: Any) -> None:
    m = res.model
    if m is Specialty:
        dup = db.scalar(select(Specialty.id).where(Specialty.program_id == obj.program_id, func.lower(Specialty.name) == obj.name.lower(), Specialty.id != (obj.id or 0)))
        if dup:
            raise HTTPException(status.HTTP_409_CONFLICT, "a specialty with that name already exists in this programme")
    if m is Subject and obj.code:
        dup = db.scalar(select(Subject.id).where(Subject.curriculum_id == obj.curriculum_id, func.lower(Subject.code) == obj.code.lower(), Subject.id != (obj.id or 0)))
        if dup:
            raise HTTPException(status.HTTP_409_CONFLICT, "a subject with that code already exists in this curriculum")


def _require_edit(db: Session, res: Resource, obj: Any, user: User) -> None:
    prog = _program_of(db, res, obj)
    inst = obj.institution if res.model is Program else (prog.institution if prog else None)
    if not can_edit_institution(user, inst):
        raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN)


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as e:  # concurrent duplicate, broken reference…
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "conflict with existing data") from e


def _overlaps(a_from, a_until, b_from, b_until) -> bool:
    lo = lambda d: d or datetime.min.date()  # noqa: E731
    hi = lambda d: d or datetime.max.date()  # noqa: E731
    return lo(a_from) <= hi(b_until) and lo(b_from) <= hi(a_until)


# ----------------------------------------------------------------------------- generic endpoints


def _register(res: Resource) -> None:
    m = res.model
    Read = res.read

    @router.get(f"/{res.path}", response_model=list[Read], name=f"list_{res.path}")
    def list_items(
        q: str | None = None,
        institution: Institution | None = None,
        program_id: int | None = None,
        curriculum_id: int | None = None,
        specialty_id: int | None = None,
        level: Level | None = None,
        kind: str | None = None,
        semester: int | None = None,
        status_: PublicationStatus | None = Query(None, alias="status"),
        validity: str | None = Query(None, pattern="^(current|upcoming|expired)$"),
        include_inactive: bool = False,
        limit: int = Query(100, ge=1, le=500),
        offset: int = Query(0, ge=0),
        user: User | None = Depends(optional_user),
        db: Session = Depends(get_db),
    ):
        stmt = _visible(res, _program_join(res, select(m)), user, include_inactive)
        if institution:
            stmt = stmt.where(Program.institution == institution)
        if program_id is not None:
            stmt = stmt.where(Program.id == program_id)
        for name, value in (("curriculum_id", curriculum_id), ("specialty_id", specialty_id), ("level", level), ("kind", kind), ("semester", semester)):
            if value not in (None, "") and name in res.filters:
                stmt = stmt.where(getattr(m, name) == value)
        if res.official and status_:
            stmt = stmt.where(m.status == status_)
        if res.official and validity:
            t = today_tn()
            stmt = stmt.where(
                {
                    "current": (or_(m.valid_from.is_(None), m.valid_from <= t)) & (or_(m.valid_until.is_(None), m.valid_until >= t)),
                    "upcoming": m.valid_from > t,
                    "expired": m.valid_until < t,
                }[validity]
            )
        if q and q.strip():
            like = f"%{q.strip().lower()}%"
            stmt = stmt.where(or_(*[func.lower(func.coalesce(getattr(m, c), "")).like(like) for c in res.search]))
        stmt = stmt.order_by(*[getattr(m, c) for c in res.order]).limit(limit).offset(offset)
        return db.scalars(stmt).all()

    @router.get(f"/{res.path}/{{item_id}}", response_model=Read, name=f"get_{res.path}")
    def get_item(item_id: int, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
        return _get(db, res, item_id, user)

    @router.post(f"/{res.path}", response_model=Read, status_code=201, name=f"create_{res.path}")
    def create_item(body: res.create, user: User = Depends(current_user), db: Session = Depends(get_db)):  # type: ignore[valid-type]
        obj = m(**body.model_dump())
        if res.official:
            obj.status = PublicationStatus.draft  # always created as a draft: publishing is an explicit action
        _check_refs(db, res, obj)
        _require_edit(db, res, obj, user)
        _check_unique(db, res, obj)
        db.add(obj)
        _commit(db)
        db.refresh(obj)
        return obj

    @router.patch(f"/{res.path}/{{item_id}}", response_model=Read, name=f"update_{res.path}")
    def update_item(item_id: int, body: res.update, user: User = Depends(current_user), db: Session = Depends(get_db)):  # type: ignore[valid-type]
        obj = _get(db, res, item_id, user)
        _require_edit(db, res, obj, user)
        changes = body.model_dump(exclude_unset=True)
        for k, v in changes.items():
            if v is None and not m.__table__.c[k].nullable:
                raise HTTPException(422, f"{k} cannot be null")
            setattr(obj, k, v)
        _check_refs(db, res, obj)
        _require_edit(db, res, obj, user)  # the new institution / curriculum must also be theirs
        _check_unique(db, res, obj)
        if res.official and obj.status == PublicationStatus.published and set(changes) - {"active"}:
            obj.status = PublicationStatus.draft  # content changed: must be reviewed and republished
            obj.published_at = None
        _commit(db)
        db.refresh(obj)
        return obj

    @router.delete(f"/{res.path}/{{item_id}}", status_code=204, name=f"delete_{res.path}")
    def delete_item(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
        obj = _get(db, res, item_id, user)
        _require_edit(db, res, obj, user)
        _cascade_delete(db, res, obj)
        _commit(db)
        return Response(status_code=204)

    if res.official:

        @router.post(f"/{res.path}/{{item_id}}/{{action}}", response_model=Read, name=f"action_{res.path}")
        def act(item_id: int, action: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
            if action not in ("publish", "archive", "draft"):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "unknown action")
            obj = _get(db, res, item_id, user)
            _require_edit(db, res, obj, user)
            if action == "publish":
                if obj.valid_until and obj.valid_until < today_tn():
                    raise HTTPException(status.HTTP_409_CONFLICT, "the validity period is already over")
                title = getattr(obj, res.title_attr)
                others = db.scalars(
                    select(m).where(
                        m.program_id == obj.program_id,
                        m.id != obj.id,
                        m.status == PublicationStatus.published,
                        (m.specialty_id.is_(None) if obj.specialty_id is None else m.specialty_id == obj.specialty_id),
                        func.lower(getattr(m, res.title_attr)) == title.lower(),
                    )
                ).all()
                if any(_overlaps(obj.valid_from, obj.valid_until, o.valid_from, o.valid_until) for o in others):
                    raise HTTPException(status.HTTP_409_CONFLICT, "another published item already covers this period")
                obj.status = PublicationStatus.published
                obj.published_at = datetime.now(timezone.utc)
            elif action == "archive":
                obj.status = PublicationStatus.archived
            else:
                obj.status = PublicationStatus.draft
                obj.published_at = None
            _commit(db)
            db.refresh(obj)
            return obj


def _cascade_delete(db: Session, res: Resource, obj: Any) -> None:
    """Delete an item and what only makes sense with it (the UI warns about this before confirming)."""
    m = res.model
    if m is Program:
        if db.scalar(select(func.count()).select_from(PreRegistration).where(PreRegistration.program_id == obj.id)):
            raise HTTPException(status.HTTP_409_CONFLICT, "this programme has pre-registrations: deactivate it instead")
        cur_ids = select(Curriculum.id).where(Curriculum.program_id == obj.id)
        db.execute(delete(PaymentTerm).where(PaymentTerm.program_id == obj.id))
        db.execute(delete(Fee).where(Fee.program_id == obj.id))
        db.execute(delete(AdmissionCondition).where(AdmissionCondition.program_id == obj.id))
        db.execute(delete(Subject).where(Subject.curriculum_id.in_(cur_ids)))
        db.execute(delete(Curriculum).where(Curriculum.program_id == obj.id))
        db.execute(delete(Specialty).where(Specialty.program_id == obj.id))
    elif m is Specialty:
        cur_ids = select(Curriculum.id).where(Curriculum.specialty_id == obj.id)
        fee_ids = select(Fee.id).where(Fee.specialty_id == obj.id)
        db.execute(delete(PaymentTerm).where(or_(PaymentTerm.specialty_id == obj.id, PaymentTerm.fee_id.in_(fee_ids))))
        db.execute(delete(Fee).where(Fee.specialty_id == obj.id))
        db.execute(delete(AdmissionCondition).where(AdmissionCondition.specialty_id == obj.id))
        db.execute(delete(Subject).where(Subject.curriculum_id.in_(cur_ids)))
        db.execute(delete(Curriculum).where(Curriculum.specialty_id == obj.id))
    elif m is Curriculum:
        db.execute(delete(Subject).where(Subject.curriculum_id == obj.id))
    elif m is Fee:
        db.execute(update(PaymentTerm).where(PaymentTerm.fee_id == obj.id).values(fee_id=None))  # keep the payment terms
    db.delete(obj)


for _res in RESOURCES.values():
    _register(_res)


@router.get("/programs/{program_id}/official-info", response_model=S.OfficialInfo)
def official_info(program_id: int, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    """What candidates and the AI agent may rely on for one formation, today: published, active, valid items only."""
    prog = db.get(Program, program_id)
    if not prog or (not prog.active and not is_staff(user)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "programme not found")

    def official(model: Any, order: Any) -> list:
        return db.scalars(select(model).where(model.program_id == program_id, *_official_now(model)).order_by(order)).all()

    fees = official(Fee, Fee.id)
    terms = official(PaymentTerm, PaymentTerm.id)
    conds = official(AdmissionCondition, AdmissionCondition.id)
    return S.OfficialInfo(
        program_id=prog.id,
        program_name=prog.name,
        institution=prog.institution,
        as_of=today_tn(),
        fees=fees,
        payment_terms=terms,
        admission_conditions=conds,
        complete={"fees": bool(fees), "payment_terms": bool(terms), "admission_conditions": bool(conds)},
    )
