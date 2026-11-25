"""Shared helpers of the catalogue routes (formations, spécialités, programmes pédagogiques, matières, conditions).

Rules (SmartCampus.pdf, section 3): an academic head manages the information of *their* institution only; the platform
administrator manages everything. Reading is public for active items; inactive ones are only visible to the team."""

from enum import Enum

from fastapi import HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.models.catalog import Specialty
from app.models.models import Institution, Program, Role, User

HEAD_SCOPE = {Role.iit_head: Institution.IIT, Role.isb_head: Institution.ISB}
manager_only = require_roles(Role.iit_head, Role.isb_head)  # the administrator always passes


class Validity(str, Enum):
    """Staff filter on the validity period of official information."""

    current = "current"
    upcoming = "upcoming"
    expired = "expired"


def scope_of(user: User) -> Institution | None:
    """Institution an academic head is limited to (None = administrator, no limit)."""
    return HEAD_SCOPE.get(user.role)


def is_staff(user: User | None) -> bool:
    return user is not None and user.role in (Role.iit_head, Role.isb_head, Role.admin)


def ensure_scope(user: User, institution: Institution) -> None:
    scope = scope_of(user)
    if scope is not None and scope != institution:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Only {institution.value} managers can change this item")


def hide_if_inactive(user: User | None, institution: Institution, *actives: bool) -> None:
    """404 for an inactive item (or one under an inactive parent) unless the viewer manages its institution."""
    if all(actives):
        return
    scope = scope_of(user) if user else None
    if not is_staff(user) or (scope is not None and scope != institution):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")


def restrict_visibility(stmt, user: User | None, include_inactive: bool, actives: list, institution_col):
    """Public: active items only. `include_inactive` needs a team account; a head also sees their institution's inactive items."""
    visible = and_(*[c.is_(True) for c in actives])
    if not include_inactive:
        return stmt.where(visible)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required for include_inactive")
    if not is_staff(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
    scope = scope_of(user)
    return stmt.where(or_(visible, institution_col == scope)) if scope else stmt


def restrict_official(stmt, model, user: User | None, include_inactive: bool, institution_col):
    """Official information (fees, payment terms, admission conditions): the public and candidates only get items that are
    published, active and valid today, under an active formation. `include_inactive` (team accounts only) also returns
    drafts, archived, upcoming and expired items of the viewer's own institution; other institutions stay official-only."""
    official = and_(model.official_clause(), Program.active.is_(True))
    if not include_inactive:
        return stmt.where(official)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required for include_inactive")
    if not is_staff(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
    scope = scope_of(user)
    return stmt.where(or_(official, institution_col == scope)) if scope else stmt


def staff_filters(stmt, model, status_filter, validity: Validity | None):
    """Optional `status` / `validity` filters (narrowing only: they can never reveal more than the visibility rule)."""
    if status_filter:
        stmt = stmt.where(model.status == status_filter)
    if validity:
        stmt = stmt.where(model.validity_clause(validity.value))
    return stmt


def hide_unless_official(user: User | None, item) -> None:
    """404 for an item that is not official today unless the viewer manages its institution."""
    hide_if_inactive(user, item.program.institution, item.official)


_ACCENTS = "àâäçéèêëîïôöùûüÿÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ"
_PLAIN = "aaaceeeeiioouuuyAAACEEEEIIOOUUUY"
_FOLD = str.maketrans(_ACCENTS, _PLAIN)


def search(stmt, q: str, *columns):
    """Case- and accent-insensitive 'contains' search over the given columns ("reseau" finds "Réseaux"; LIKE wildcards in
    `q` are escaped). Folding uses translate(), built into PostgreSQL (no extension) and registered for SQLite in db/session.py."""
    term = q.strip()
    if not term:
        return stmt
    esc = term.translate(_FOLD).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return stmt.where(or_(*[func.translate(c, _ACCENTS, _PLAIN).ilike(f"%{esc}%", escape="\\") for c in columns]))


def page(db: Session, stmt, response: Response, limit: int, offset: int):
    """Run a paginated list query; the total number of matches is returned in the `X-Total-Count` header."""
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    response.headers["X-Total-Count"] = str(total or 0)
    return db.scalars(stmt.limit(limit).offset(offset)).all()


def get_or_404(db: Session, model, item_id: int, label: str):
    obj = db.get(model, item_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{label} not found")
    return obj


def apply_update(obj, body: BaseModel, nullable: frozenset[str] = frozenset()) -> None:
    """PATCH semantics: only the fields sent are changed; sending null is only allowed on optional columns."""
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is None and field not in nullable:
            raise HTTPException(422, f"'{field}' cannot be null")
        setattr(obj, field, value)


def check_specialty(db: Session, specialty_id: int | None, program_id: int) -> None:
    if specialty_id is None:
        return
    specialty = db.get(Specialty, specialty_id)
    if specialty is None or specialty.program_id != program_id:
        raise HTTPException(422, "Specialty does not belong to this formation")
