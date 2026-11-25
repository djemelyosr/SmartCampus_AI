import json
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.core.config import settings
from app.models.models import Conversation, Message, User
from app.schemas.schemas import ConversationOut, MessageIn, MessageOut
from app.services import session_memory
from app.services.orchestrator import run_agent, run_guest

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _own(db: Session, conv_id: int, user: User) -> Conversation:
    conv = db.get(Conversation, conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(404, "Conversation not found")
    return conv


# --- Chat without an account ---------------------------------------------------------------------------------------------
# Same agent, nothing stored: the profile slots, the bounded working memory and the language go back to the browser with every
# answer and come back with the next question. Declared before "/{conv_id}/..." so that "guest" is never read as an id.
_guest_hits: dict[str, deque[float]] = defaultdict(deque)


class GuestMessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    modality: str = "text"
    state: dict | None = None  # what the previous answer returned (untrusted: bounded and validated by the agent)


class GuestMessageOut(BaseModel):
    content: str
    meta: dict
    state: dict


def _client(request: Request) -> str:
    return request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "?")


def _guest_allowed(client: str) -> bool:
    now = time.monotonic()
    hits = _guest_hits[client]
    while hits and now - hits[0] > 60:
        hits.popleft()
    if len(hits) >= settings.guest_messages_per_minute:
        return False
    hits.append(now)
    return True


@router.post("/guest/messages", response_model=GuestMessageOut)
def guest_message(body: GuestMessageIn, request: Request, db: Session = Depends(get_db)):
    if not _guest_allowed(_client(request)):
        raise HTTPException(429, "Too many messages: wait a moment or sign in")
    if body.state is not None and len(json.dumps(body.state, ensure_ascii=False).encode()) > settings.guest_max_state_bytes:
        raise HTTPException(413, "Conversation state too large")
    try:
        reply, state = run_guest(db, body.content, body.state)
    except HTTPException:
        raise
    except Exception:  # a tampered state must not become a server error: start again from an empty one
        reply, state = run_guest(db, body.content, None)
    return {"content": reply["content"], "meta": reply.get("meta", {}), "state": state}


@router.post("", response_model=ConversationOut, status_code=201)
def start(user: User = Depends(current_user), db: Session = Depends(get_db)):
    conv = Conversation(user_id=user.id)
    db.add(conv)
    db.commit()
    return conv


@router.get("", response_model=list[ConversationOut])
def mine(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Conversation).where(Conversation.user_id == user.id)).all()


@router.get("/{conv_id}", response_model=ConversationOut)
def get(conv_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _own(db, conv_id, user)


@router.get("/{conv_id}/memory")
def memory(conv_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """What the agent temporarily remembers of this conversation (redacted, bounded, expiring)."""
    _own(db, conv_id, user)
    row = session_memory.peek(db, conv_id)
    if row is None:
        return {"active": False, "turns": [], "context": None, "expires_at": None, "expires_in_seconds": 0}
    return session_memory.describe(row)


@router.delete("/{conv_id}/memory", status_code=204)
def forget(conv_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """The candidate asks the agent to forget the working memory (messages and profile history are untouched)."""
    _own(db, conv_id, user)
    session_memory.forget(db, conv_id)
    db.commit()


@router.post("/{conv_id}/messages", response_model=MessageOut)
def send(conv_id: int, body: MessageIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conv = _own(db, conv_id, user)
    db.add(Message(conversation_id=conv.id, role="user", content=body.content, modality=body.modality))
    db.flush()
    reply = run_agent(db, conv, user, body.content)
    msg = Message(conversation_id=conv.id, role="assistant", content=reply["content"], meta=reply.get("meta", {}))
    db.add(msg)
    db.commit()
    return msg
