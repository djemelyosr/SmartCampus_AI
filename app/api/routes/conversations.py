"""Chat conversations, open to everyone.

- Signed-in user (Bearer token): the conversation belongs to the account.
- Visitor without account: send the `X-Guest-Session` token received earlier. Without it, the first
  `POST /conversations` creates a visitor session automatically and returns its token (header + body).
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import optional_user
from app.db.session import get_db
from app.models.models import Conversation, GuestSession, Message, User
from app.schemas.schemas import ConversationOut, MessageIn, MessageOut
from app.services import guest
from app.services.orchestrator import run_agent

router = APIRouter(prefix="/conversations", tags=["conversations"])
USER_MESSAGE_MAX_CHARS = 4000


class GuestSessionOut(BaseModel):
    id: str
    token: str | None = None  # only returned when the session has just been created
    expires_at: datetime
    messages_left: int


class ConversationStartOut(ConversationOut):
    guest_session: GuestSessionOut | None = None


def _owned(db: Session, conv_id: int, user: User | None, token: str | None) -> tuple[Conversation, GuestSession | None]:
    conv = db.get(Conversation, conv_id)
    if conv and user and conv.user_id == user.id:
        return conv, None
    if conv and not user and conv.user_id is None and token:
        s = guest.require_active(db, token)
        if conv.guest_session_id == s.id:
            return conv, s
    raise HTTPException(404, "Conversation not found")


@router.post("", response_model=ConversationStartOut, status_code=201)
def start(
    request: Request,
    response: Response,
    user: User | None = Depends(optional_user),
    x_guest_session: str | None = Header(None),
    db: Session = Depends(get_db),
):
    if user:
        conv = Conversation(user_id=user.id)
        db.add(conv)
        db.commit()
        return ConversationStartOut.model_validate(conv)

    token, created = x_guest_session, False
    if token:
        s = guest.require_active(db, token)
    else:
        s, token = guest.create(db, request.client.host if request.client else None)
        created = True
    guest.check_new_conversation(db, s)
    guest.touch(s)
    conv = Conversation(guest_session_id=s.id)
    db.add(conv)
    db.commit()
    if created:
        response.headers[guest.HEADER] = token
    out = ConversationStartOut.model_validate(conv)
    out.guest_session = GuestSessionOut(id=s.id, token=token if created else None, expires_at=guest.aware(s.expires_at), messages_left=guest.info(db, s)["messages_left"])
    return out


@router.get("", response_model=list[ConversationOut])
def mine(user: User | None = Depends(optional_user), x_guest_session: str | None = Header(None), db: Session = Depends(get_db)):
    if user:
        return db.scalars(select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.id)).all()
    if x_guest_session:
        s = guest.require_active(db, x_guest_session)
        return db.scalars(select(Conversation).where(Conversation.guest_session_id == s.id, Conversation.user_id.is_(None)).order_by(Conversation.id)).all()
    raise HTTPException(401, "Not authenticated")


@router.get("/{conv_id}", response_model=ConversationOut)
def get(conv_id: int, user: User | None = Depends(optional_user), x_guest_session: str | None = Header(None), db: Session = Depends(get_db)):
    return _owned(db, conv_id, user, x_guest_session)[0]


@router.post("/{conv_id}/messages", response_model=MessageOut)
def send(
    conv_id: int,
    body: MessageIn,
    user: User | None = Depends(optional_user),
    x_guest_session: str | None = Header(None),
    db: Session = Depends(get_db),
):
    content = body.content.strip()
    if not content:
        raise HTTPException(422, "Empty message")
    conv, s = _owned(db, conv_id, user, x_guest_session)
    if s:
        guest.check_new_message(db, s, content)
        s.message_count += 1
        guest.touch(s)
    elif len(content) > USER_MESSAGE_MAX_CHARS:
        raise HTTPException(422, f"Message too long (max {USER_MESSAGE_MAX_CHARS} characters)")
    db.add(Message(conversation_id=conv.id, role="user", content=content, modality=body.modality))
    db.flush()
    reply = run_agent(db, conv, user, content)
    msg = Message(conversation_id=conv.id, role="assistant", content=reply["content"], meta=reply.get("meta", {}))
    db.add(msg)
    db.commit()
    return msg
