from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.models.models import ApprovalStatus, CandidateProfile, Role, User
from app.schemas.schemas import AccessApproval, AccountStatusUpdate, AdminUserCreate, AdminUserUpdate, UserOut

# Platform administrator: manage accounts, roles and access rights (SmartCampus.pdf, section 3).
router = APIRouter(prefix="/admin/users", tags=["admin"])
admin_only = require_roles(Role.admin)


def _active_admins(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User).where(User.role == Role.admin, User.is_active.is_(True))) or 0


@router.get("", response_model=list[UserOut])
def list_users(
    q: str = "", role: Role | None = None, approval: ApprovalStatus | None = None,  # approval=pending: access requests to review
    db: Session = Depends(get_db), _: User = Depends(admin_only),
):
    stmt = select(User).order_by(User.id)
    if role:
        stmt = stmt.where(User.role == role)
    if approval:
        stmt = stmt.where(User.approval_status == approval)
    if q.strip():
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(User.email).like(like), func.lower(User.full_name).like(like)))
    return db.scalars(stmt).all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(body: AdminUserCreate, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(email=body.email, full_name=body.full_name, role=body.role, hashed_password=hash_password(body.password))
    if body.role == Role.candidate:
        user.profile = CandidateProfile()
    db.add(user)
    db.commit()
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: AdminUserUpdate, db: Session = Depends(get_db), me: User = Depends(admin_only)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    losing_admin = user.role == Role.admin and user.is_active and (
        (body.role is not None and body.role != Role.admin) or body.is_active is False
    )
    if losing_admin and (user.id == me.id or _active_admins(db) <= 1):
        raise HTTPException(status.HTTP_409_CONFLICT, "At least one active administrator is required")
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.role is not None:
        user.role = body.role
        if body.role == Role.candidate and user.profile is None:
            user.profile = CandidateProfile()
    if body.is_active is not None:
        user.is_active = body.is_active
        if body.is_active:
            _clear_block(user)
    if body.password:
        user.hashed_password = hash_password(body.password)
    db.commit()
    return user


def _clear_block(user: User) -> None:
    user.is_blocked, user.blocked_reason, user.blocked_at, user.blocked_by_id = False, None, None, None


@router.put("/{user_id}/status", response_model=UserOut)
def set_account_status(user_id: int, body: AccountStatusUpdate, db: Session = Depends(get_db), me: User = Depends(admin_only)):
    """Account state of an approved account (sign-in and already issued tokens are refused as soon as it is not `active`):
    - `active`: can sign in;
    - `inactive`: switched off, can be reactivated at any time;
    - `blocked`: refused, with a reason, the date and the administrator kept on the record.
    An administrator cannot change the state of their own account (so the platform always keeps an active administrator)."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.approval_status != ApprovalStatus.approved:
        raise HTTPException(status.HTTP_409_CONFLICT, "Account not approved: approve or reject its access request first")
    if user.id == me.id and body.status != "active":
        raise HTTPException(status.HTTP_409_CONFLICT, "Cannot change your own status")
    if body.status == "active":
        user.is_active = True
        _clear_block(user)
    elif body.status == "inactive":
        user.is_active = False
        _clear_block(user)
    else:
        user.is_active, user.is_blocked = False, True
        user.blocked_reason, user.blocked_at, user.blocked_by_id = (body.reason or None), datetime.now(timezone.utc), me.id
    db.commit()
    return user


def _decide(db: Session, user_id: int, reviewer: User, status_: ApprovalStatus, note: str | None, allowed: set[ApprovalStatus]) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.approval_status not in allowed:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Request already {user.approval_status.value}")
    user.approval_status = status_
    user.reviewed_by_id, user.reviewed_at, user.review_note = reviewer.id, datetime.now(timezone.utc), (note or None)
    return user


@router.post("/{user_id}/approve", response_model=UserOut)
def approve_access(user_id: int, body: AccessApproval | None = None, db: Session = Depends(get_db), me: User = Depends(admin_only)):
    """Grant access: the account gets the requested role (or the one the administrator picks). A rejected request can be
    reconsidered; an already approved account is changed through PATCH instead."""
    body = body or AccessApproval()
    user = _decide(db, user_id, me, ApprovalStatus.approved, body.note, {ApprovalStatus.pending, ApprovalStatus.rejected})
    user.role = body.role or user.requested_role or Role.candidate
    user.is_active = True
    if user.role == Role.candidate and user.profile is None:
        user.profile = CandidateProfile()
    db.commit()
    return user


@router.post("/{user_id}/reject", response_model=UserOut)
def reject_access(user_id: int, body: AccessApproval | None = None, db: Session = Depends(get_db), me: User = Depends(admin_only)):
    """Refuse a pending request: the account stays a candidate account that cannot sign in; the note is kept for the record."""
    user = _decide(db, user_id, me, ApprovalStatus.rejected, (body or AccessApproval()).note, {ApprovalStatus.pending})
    db.commit()
    return user
