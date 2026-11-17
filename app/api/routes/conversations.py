from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.models import Conversation, Message, User
from app.schemas.schemas import ConversationOut, MessageIn, MessageOut
from app.services.orchestrator import run_agent

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _own(db: Session, conv_id: int, user: User) -> Conversation:
    conv = db.get(Conversation, conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(404, "Conversation not found")
    return conv


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
