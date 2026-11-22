from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import candidate_user, current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.models import CandidateProfile, Role, User
from app.schemas.schemas import ProfileIn, ProfileOut, Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

# Hash used when the e-mail is unknown, so login takes the same time either way (no account enumeration by timing).
_DUMMY_HASH = hash_password("dummy-password-for-timing")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def email_taken(db: Session, email: str) -> bool:
    return db.scalar(select(User.id).where(func.lower(User.email) == normalize_email(email))) is not None


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    """Public sign-up. Always a candidate account: team roles are granted by an administrator."""
    if email_taken(db, body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(email=normalize_email(body.email), full_name=body.full_name.strip(), hashed_password=hash_password(body.password), role=Role.candidate)
    user.profile = CandidateProfile()
    db.add(user)
    db.commit()
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.email) == normalize_email(form.username)))
    ok = verify_password(form.password, user.hashed_password if user else _DUMMY_HASH)
    if not user or not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bad credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account suspended")
    return Token(access_token=create_access_token(str(user.id), user.role.value))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.get("/me/profile", response_model=ProfileOut)
def get_profile(user: User = Depends(candidate_user), db: Session = Depends(get_db)):
    if user.profile is None:
        user.profile = CandidateProfile()
        db.commit()
    return user.profile


@router.put("/me/profile", response_model=ProfileOut)
def update_profile(body: ProfileIn, user: User = Depends(candidate_user), db: Session = Depends(get_db)):
    if user.profile is None:
        user.profile = CandidateProfile()
    for k, v in body.model_dump().items():
        setattr(user.profile, k, v)
    db.add(user)
    db.commit()
    return user.profile
