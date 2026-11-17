from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.models import CandidateProfile, User
from app.schemas.schemas import ProfileIn, ProfileOut, Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(email=body.email, full_name=body.full_name, hashed_password=hash_password(body.password))
    user.profile = CandidateProfile()
    db.add(user)
    db.commit()
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bad credentials")
    return Token(access_token=create_access_token(str(user.id), user.role.value))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.get("/me/profile", response_model=ProfileOut)
def get_profile(user: User = Depends(current_user)):
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
