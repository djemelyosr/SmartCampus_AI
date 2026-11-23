"""Visitor sessions and attaching a visitor conversation to a candidate account.

Flow when a visitor signs up or signs in after chatting:
1. The client keeps the visitor token (`X-Guest-Session`).
2. After sign-in it calls `GET /guest/claim/preview` (Bearer + visitor token) to show what would be kept.
3. Only if the person explicitly agrees, it calls `POST /guest/claim` with `consent: true`.
   Ownership is verified by the token itself: only the browser that holds it can claim the session.
4. If the person declines, `DELETE /guest/session` erases the visitor conversation.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import candidate_user
from app.core.config import settings
from app.db.session import get_db
from app.models.models import Conversation, GuestStatus, Message, User
from app.services import guest

router = APIRouter(prefix="/guest", tags=["visitor sessions"])


class SessionInfo(BaseModel):
    id: str
    status: str
    expires_at: datetime
    messages_used: int
    messages_left: int
    conversation_ids: list[int]
    token: str | None = None


class ClaimIn(BaseModel):
    consent: bool
    guest_token: str | None = None  # alternatively sent in the X-Guest-Session header


class ClaimPreview(BaseModel):
    session_id: str
    conversations: int
    messages: int
    first_message: str | None
    expires_at: datetime
    consent_text: str


CONSENT_TEXT = (
    "Associer cette conversation à votre compte candidat : elle sera conservée dans votre espace et pourra être "
    "consultée par l’équipe habilitée pour vous accompagner. Vous pouvez aussi refuser : elle sera alors supprimée."
)


def _token(header: str | None, body_token: str | None = None) -> str:
    tok = body_token or header
    if not tok:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Visitor session token required (X-Guest-Session)")
    return tok


@router.get("/limits")
def limits():
    """Public: the rules applied to visitor sessions (useful to display them)."""
    return {
        "idle_minutes": settings.guest_idle_minutes,
        "max_hours": settings.guest_max_hours,
        "max_messages": settings.guest_max_messages,
        "max_conversations": settings.guest_max_conversations,
        "messages_per_minute": settings.guest_messages_per_minute,
        "message_max_chars": settings.guest_message_max_chars,
    }


@router.post("/sessions", response_model=SessionInfo, status_code=201)
def create_session(request: Request, response: Response, db: Session = Depends(get_db)):
    """Explicitly open a visitor session (otherwise it is created by the first `POST /conversations`)."""
    s, token = guest.create(db, request.client.host if request.client else None)
    db.commit()
    response.headers[guest.HEADER] = token
    return SessionInfo(**guest.info(db, s), token=token)


@router.get("/session", response_model=SessionInfo)
def get_session(x_guest_session: str | None = Header(None), db: Session = Depends(get_db)):
    return SessionInfo(**guest.info(db, guest.require_active(db, _token(x_guest_session))))


@router.delete("/session", status_code=204)
def discard_session(x_guest_session: str | None = Header(None), db: Session = Depends(get_db)):
    """Forget the visitor session and its conversations (visitor's choice, or refusal to attach it)."""
    s = guest.find(db, _token(x_guest_session))
    if s is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid visitor session")
    if s.status == GuestStatus.claimed:
        raise HTTPException(status.HTTP_409_CONFLICT, "This visitor session is already attached to an account")
    guest.discard(db, s)
    return Response(status_code=204)


@router.get("/claim/preview", response_model=ClaimPreview)
def claim_preview(user: User = Depends(candidate_user), x_guest_session: str | None = Header(None), db: Session = Depends(get_db)):
    """What would be attached to the signed-in candidate, to ask for their agreement."""
    s = guest.require_active(db, _token(x_guest_session))
    conv_ids = select(Conversation.id).where(Conversation.guest_session_id == s.id, Conversation.user_id.is_(None))
    first = db.scalar(select(Message.content).where(Message.conversation_id.in_(conv_ids), Message.role == "user").order_by(Message.id))
    return ClaimPreview(
        session_id=s.id,
        conversations=db.scalar(select(func.count()).select_from(Conversation).where(Conversation.id.in_(conv_ids))),
        messages=db.scalar(select(func.count()).select_from(Message).where(Message.conversation_id.in_(conv_ids))),
        first_message=(first[:160] + "…") if first and len(first) > 160 else first,
        expires_at=guest.aware(s.expires_at),
        consent_text=CONSENT_TEXT,
    )


@router.post("/claim")
def claim(body: ClaimIn, user: User = Depends(candidate_user), x_guest_session: str | None = Header(None), db: Session = Depends(get_db)):
    """Attach the visitor session's conversations to the signed-in candidate, with explicit consent."""
    if body.consent is not True:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Explicit consent is required to attach the visitor conversation")
    s = guest.require_active(db, _token(x_guest_session, body.guest_token))  # holding the token proves ownership
    convs = db.scalars(select(Conversation).where(Conversation.guest_session_id == s.id, Conversation.user_id.is_(None))).all()
    for c in convs:
        c.user_id = user.id  # guest_session_id is kept as provenance
    t = guest.now()
    s.status, s.claimed_by_user_id, s.claimed_at, s.claim_consent_at = GuestStatus.claimed, user.id, t, t
    db.commit()
    return {
        "session_id": s.id,
        "attached_conversation_ids": [c.id for c in convs],
        "messages": sum(len(c.messages) for c in convs),
    }
