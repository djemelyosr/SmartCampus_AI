from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.models import ApprovalStatus, CandidateProfile, Role, User
from app.schemas.schemas import SELF_REGISTER_ROLES, ProfileIn, ProfileOut, Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/register/roles")
def register_roles():
    """Roles a visitor can pick at sign-up. Only `candidate` is immediate; the others wait for an administrator."""
    return [{"role": r.value, "needs_approval": r != Role.candidate} for r in SELF_REGISTER_ROLES]


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(email=body.email, full_name=body.full_name, hashed_password=hash_password(body.password))
    if body.role == Role.candidate:
        user.profile = CandidateProfile()
    else:
        # Least privilege until an administrator decides: the account stays a candidate account and cannot sign in.
        user.requested_role = body.role
        user.approval_status = ApprovalStatus.pending
    db.add(user)
    db.commit()
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bad credentials")
    if user.approval_status == ApprovalStatus.pending:  # only revealed once the password is right
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account pending approval")
    if user.approval_status == ApprovalStatus.rejected:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account request rejected")
    if user.is_blocked:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account blocked")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    return Token(access_token=create_access_token(str(user.id), user.role.value))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.get("/me/profile", response_model=ProfileOut)
def get_profile(user: User = Depends(current_user)):
    if user.profile is None:  # staff / admin accounts have no candidate profile (it is created on first save)
        raise HTTPException(404, "No candidate profile for this account")
    return user.profile


@router.put("/me/profile", response_model=ProfileOut)
def update_profile(body: ProfileIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.profile is None:
        user.profile = CandidateProfile()
    for k, v in body.model_dump().items():
        setattr(user.profile, k, v)
    db.add(user)
    db.commit()
    return user.profile
