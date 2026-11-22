"""Administrator: accounts, roles and access (screen 24)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.routes.auth import email_taken, normalize_email
from app.core.security import hash_password
from app.db.session import get_db
from app.models.models import CandidateProfile, Role, User
from app.schemas.schemas import AdminUserCreate, AdminUserUpdate, UserOut

router = APIRouter(prefix="/admin/users", tags=["admin"])
admin_only = require_roles(Role.admin)


def _active_admins(db: Session) -> int:
    return len(db.scalars(select(User.id).where(User.role == Role.admin, User.is_active.is_(True))).all())


@router.get("", response_model=list[UserOut])
def list_users(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.id)).all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(body: AdminUserCreate, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    if email_taken(db, body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(email=normalize_email(body.email), full_name=body.full_name.strip(), role=body.role, hashed_password=hash_password(body.password))
    if body.role == Role.candidate:
        user.profile = CandidateProfile()
    db.add(user)
    db.commit()
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: AdminUserUpdate, me: User = Depends(admin_only), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    changes = body.model_dump(exclude_unset=True)
    if user.id == me.id and changes.get("is_active") is False:
        raise HTTPException(status.HTTP_409_CONFLICT, "You cannot suspend your own account")
    loses_admin = user.role == Role.admin and user.is_active and (
        changes.get("is_active") is False or (changes.get("role") not in (None, Role.admin))
    )
    if loses_admin and _active_admins(db) <= 1:
        raise HTTPException(status.HTTP_409_CONFLICT, "At least one active administrator must remain")
    if "full_name" in changes and changes["full_name"] is not None:
        user.full_name = changes["full_name"].strip()
    if changes.get("role") is not None:
        user.role = changes["role"]
        if user.role == Role.candidate and user.profile is None:
            user.profile = CandidateProfile()
    if changes.get("is_active") is not None:
        user.is_active = changes["is_active"]
    if changes.get("password"):
        user.hashed_password = hash_password(changes["password"])
    db.commit()
    return user
