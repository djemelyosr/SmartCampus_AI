"""Single entry point to the OFFICIAL information of a formation: fees, payment terms and admission conditions that are
published, active and valid on a given day. The public API and the AI agent both read through here, so a draft, an
archived item or an expired / not-yet-valid tariff can never reach a candidate."""

from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.dates import tn_today
from app.models.catalog import AdmissionCondition, Fee, PaymentTerm
from app.models.models import Program


def _official(db: Session, model, program_id: int, on: date, specialty_id: int | None) -> list:
    stmt = select(model).where(model.program_id == program_id, model.official_clause(on))
    if specialty_id is not None:  # the whole formation + this specialty
        stmt = stmt.where(or_(model.specialty_id.is_(None), model.specialty_id == specialty_id))
    rows = db.scalars(stmt).all()
    return sorted(rows, key=lambda r: (r.specialty_id is not None, r.specialty_id or 0, r.id))  # formation-wide first


def official_info(db: Session, program: Program, specialty_id: int | None = None, on: date | None = None) -> dict:
    """Official items of a formation. Nothing is returned for an inactive formation."""
    on = on or tn_today()
    if not program.active:
        fees, terms, conditions = [], [], []
    else:
        fees = _official(db, Fee, program.id, on, specialty_id)
        terms = _official(db, PaymentTerm, program.id, on, specialty_id)
        conditions = _official(db, AdmissionCondition, program.id, on, specialty_id)
    return {
        "program": program,
        "as_of": on,
        "fees": fees,
        "payment_terms": terms,
        "admission_conditions": conditions,
        "complete": {"fees": bool(fees), "payment_terms": bool(terms), "admission_conditions": bool(conditions)},
    }
