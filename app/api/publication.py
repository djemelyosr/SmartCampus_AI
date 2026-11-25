"""Publication workflow shared by fees, payment terms and admission conditions.

draft  --publish-->  published  --archive-->  archived          (draft is reachable from any state)

* Only the academic head of the formation's institution (or the administrator) can change a status.
* Editing the content of a published item (anything but `active`) sends it back to draft: what candidates and the agent
  see was always approved by a human, and must be re-published after a change.
* Two published items of the same formation / specialty / title cannot cover the same days: a new tariff takes over by
  starting the day after the previous one ends (or by archiving it)."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.catalog import apply_update, ensure_scope, get_or_404, manager_only
from app.core.dates import tn_today
from app.db.session import get_db
from app.models.catalog import PublicationStatus
from app.models.models import User

PERIOD_FIELDS = frozenset({"valid_from", "valid_until", "academic_year"})


def check_publishable(db: Session, item, key_field: str) -> None:
    """422 if the validity period is already over, 409 if another published item covers the same days."""
    model = type(item)
    if item.valid_until is not None and item.valid_until < tn_today():
        raise HTTPException(422, "The validity period is already over: extend valid_until before publishing")
    key = getattr(item, key_field)
    same_scope = model.specialty_id.is_(None) if item.specialty_id is None else model.specialty_id == item.specialty_id
    rivals = db.scalars(
        select(model).where(
            model.program_id == item.program_id,
            same_scope,
            getattr(model, key_field) == key,
            model.status == PublicationStatus.published,
            model.active.is_(True),
            model.id != item.id,
        )
    ).all()
    start, end = item.valid_from or date.min, item.valid_until or date.max
    for other in rivals:
        if (other.valid_from or date.min) <= end and start <= (other.valid_until or date.max):
            raise HTTPException(
                409,
                f"Another published item '{key}' (id {other.id}) already covers this period: "
                "archive it or adjust the validity periods",
            )


def publish(db: Session, item, user: User, key_field: str) -> None:
    if item.status == PublicationStatus.published:
        return
    check_publishable(db, item, key_field)
    item.status = PublicationStatus.published
    item.published_at = datetime.now(timezone.utc)
    item.published_by_id = user.id


def to_draft(item) -> None:
    item.status = PublicationStatus.draft
    item.published_at = None
    item.published_by_id = None


def update_official(item, body: BaseModel, nullable: frozenset[str]) -> bool:
    """PATCH an official item. Returns True when a published item went back to draft because its content changed."""
    changed = set(body.model_fields_set)
    apply_update(item, body, nullable=nullable | PERIOD_FIELDS)
    if item.valid_from and item.valid_until and item.valid_until < item.valid_from:
        raise HTTPException(422, "valid_until must not be before valid_from")
    if item.status == PublicationStatus.published and changed - {"active"}:
        to_draft(item)
        return True
    return False


def add_workflow_routes(router: APIRouter, model, label: str, out, key_field: str) -> None:
    """Register POST /{id}/publish, /{id}/archive and /{id}/draft on a catalogue router."""

    def load(db: Session, item_id: int, user: User):
        item = get_or_404(db, model, item_id, label)
        ensure_scope(user, item.program.institution)
        return item

    @router.post("/{item_id}/publish", response_model=out, summary=f"Publish a {label.lower()} (official from valid_from)")
    def publish_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(manager_only)):
        item = load(db, item_id, user)
        publish(db, item, user, key_field)
        db.commit()
        return item

    @router.post("/{item_id}/archive", response_model=out, summary=f"Withdraw a {label.lower()} (kept for history)")
    def archive_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(manager_only)):
        item = load(db, item_id, user)
        item.status = PublicationStatus.archived
        db.commit()
        return item

    @router.post("/{item_id}/draft", response_model=out, summary=f"Take a {label.lower()} back to draft")
    def draft_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(manager_only)):
        item = load(db, item_id, user)
        to_draft(item)
        db.commit()
        return item
