"""Authentication and authorisation helpers shared by every route.

- `current_user`: a valid, non-suspended account is required (401 / 403 otherwise).
- `optional_user`: same checks when a token is sent, but visitors without a token are allowed (public chat).
- `require_roles(...)`: role-based access; the administrator always passes.
- `institution_scope` / `can_edit_institution`: academic heads only manage their own institution.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.models import Institution, Role, User

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

HEADS = {Role.iit_head: Institution.IIT, Role.isb_head: Institution.ISB}
CATALOG_EDITORS = (Role.iit_head, Role.isb_head)  # + admin (implicit)
STAFF = {Role.iit_head, Role.isb_head, Role.interviewer, Role.direction, Role.admin}


def _user_from_token(token: str, db: Session) -> User:
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    user = db.get(User, int(payload.get("sub", 0)))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found", headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account suspended")
    return user


def current_user(token: str | None = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    return _user_from_token(token, db)


def optional_user(token: str | None = Depends(oauth2), db: Session = Depends(get_db)) -> User | None:
    """Visitor-friendly: no token -> None. A token that is sent must still be valid."""
    return _user_from_token(token, db) if token else None


def require_roles(*roles: Role):
    def checker(user: User = Depends(current_user)) -> User:
        if user.role not in roles and user.role != Role.admin:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return checker


def is_staff(user: User | None) -> bool:
    return bool(user and user.role in STAFF)


def institution_scope(user: User) -> Institution | None:
    """The only institution an academic head may manage; None = every institution (administrator)."""
    return HEADS.get(user.role)


def can_edit_institution(user: User, institution: Institution | str | None) -> bool:
    if user.role == Role.admin:
        return True
    own = HEADS.get(user.role)
    return own is not None and institution is not None and Institution(institution) == own


def candidate_user(user: User = Depends(current_user)) -> User:
    """Candidate journey (profile, pre-registration, QCM, appointments, documents): candidate accounts only."""
    if user.role != Role.candidate:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Candidate account required")
    return user
