"""Visitor (guest) sessions for the public chat.

A session is created automatically when a visitor without an account starts a conversation. The client
receives a token `<session_id>.<secret>` (header `X-Guest-Session`) and sends it back on every call; we only
store a SHA-256 hash of the secret. Possession of the token is what proves the session belongs to the caller,
which is also the check used before attaching the session to a candidate account.

Validity: sliding expiry after `guest_idle_minutes` of inactivity, capped at `guest_max_hours` after creation.
Limits: messages per session, conversations per session, messages per minute, new sessions per network address.
Expired sessions are marked `expired`, then deleted with their conversations after `guest_retention_hours`
unless they were attached to an account.
"""

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Conversation, GuestSession, GuestStatus, Message

HEADER = "X-Guest-Session"


def now() -> datetime:
    return datetime.now(timezone.utc)


def aware(dt: datetime | None) -> datetime | None:
    """Treat a naive datetime as UTC (columns are timestamptz, but values set in Python may still be naive)."""
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _hash(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def client_fingerprint(ip: str | None) -> str | None:
    """Salted hash of the network address: enough for rate limits, the address itself is never stored."""
    return hmac.new(settings.secret_key.encode(), (ip or "unknown").encode(), hashlib.sha256).hexdigest() if ip else None


def _deadline(created: datetime, last_seen: datetime) -> datetime:
    return min(created + timedelta(hours=settings.guest_max_hours), last_seen + timedelta(minutes=settings.guest_idle_minutes))


def create(db: Session, ip: str | None) -> tuple[GuestSession, str]:
    fp = client_fingerprint(ip)
    if fp:
        recent = db.scalar(
            select(func.count()).select_from(GuestSession).where(GuestSession.client_hash == fp, GuestSession.created_at >= now() - timedelta(hours=1))
        )
        if recent >= settings.guest_sessions_per_hour_per_client:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many visitor sessions from this network, please try again later")
    t = now()
    sid, secret = uuid.uuid4().hex, secrets.token_urlsafe(32)
    s = GuestSession(id=sid, secret_hash=_hash(secret), status=GuestStatus.active, created_at=t, last_seen_at=t, expires_at=_deadline(t, t), client_hash=fp)
    db.add(s)
    db.flush()
    return s, f"{sid}.{secret}"


def find(db: Session, token: str | None) -> GuestSession | None:
    """Session matching the token (constant-time check of the secret), whatever its status; None if no match."""
    if not token or "." not in token:
        return None
    sid, secret = token.split(".", 1)
    s = db.get(GuestSession, sid[:32])
    if not s or not hmac.compare_digest(s.secret_hash, _hash(secret)):
        return None
    return s


def require_active(db: Session, token: str | None) -> GuestSession:
    s = find(db, token)
    if s is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid visitor session")
    if s.status == GuestStatus.claimed:
        raise HTTPException(status.HTTP_409_CONFLICT, "This visitor session is already attached to an account")
    if s.status == GuestStatus.expired or aware(s.expires_at) <= now():
        s.status = GuestStatus.expired
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Visitor session expired: start a new conversation")
    return s


def touch(s: GuestSession) -> None:
    """Activity extends the session (sliding expiry), never beyond the maximum lifetime."""
    t = now()
    s.last_seen_at = t
    s.expires_at = _deadline(aware(s.created_at) or t, t)


def check_new_conversation(db: Session, s: GuestSession) -> None:
    n = db.scalar(select(func.count()).select_from(Conversation).where(Conversation.guest_session_id == s.id))
    if n >= settings.guest_max_conversations:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Conversation limit reached for this visitor session")


def check_new_message(db: Session, s: GuestSession, content: str) -> None:
    if len(content) > settings.guest_message_max_chars:
        raise HTTPException(422, f"Message too long (max {settings.guest_message_max_chars} characters)")
    if s.message_count >= settings.guest_max_messages:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Message limit reached for this visitor session: create an account to continue")
    last_minute = db.scalar(
        select(func.count())
        .select_from(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.guest_session_id == s.id, Message.role == "user", Message.created_at >= now() - timedelta(minutes=1))
    )
    if last_minute >= settings.guest_messages_per_minute:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many messages, please slow down")


def info(db: Session, s: GuestSession) -> dict:
    convs = db.scalars(select(Conversation).where(Conversation.guest_session_id == s.id).order_by(Conversation.id)).all()
    return {
        "id": s.id,
        "status": s.status.value,
        "expires_at": aware(s.expires_at),
        "messages_used": s.message_count,
        "messages_left": max(settings.guest_max_messages - s.message_count, 0),
        "conversation_ids": [c.id for c in convs],
    }


def purge_expired(db: Session) -> dict:
    """Mark sessions past their deadline as expired; delete unclaimed expired sessions past the retention delay."""
    t = now()
    marked = db.execute(
        update(GuestSession).where(GuestSession.status == GuestStatus.active, GuestSession.expires_at <= t).values(status=GuestStatus.expired)
    ).rowcount
    old = select(GuestSession.id).where(GuestSession.status == GuestStatus.expired, GuestSession.expires_at <= t - timedelta(hours=settings.guest_retention_hours))
    conv_ids = select(Conversation.id).where(Conversation.guest_session_id.in_(old), Conversation.user_id.is_(None))
    db.execute(delete(Message).where(Message.conversation_id.in_(conv_ids)))
    db.execute(delete(Conversation).where(Conversation.guest_session_id.in_(old), Conversation.user_id.is_(None)))
    deleted = db.execute(delete(GuestSession).where(GuestSession.id.in_(old))).rowcount
    db.commit()
    return {"expired": marked or 0, "deleted": deleted or 0}


def discard(db: Session, s: GuestSession) -> None:
    """The visitor asks to forget the session (or declines to attach it): delete it with its conversations."""
    conv_ids = select(Conversation.id).where(Conversation.guest_session_id == s.id, Conversation.user_id.is_(None))
    db.execute(delete(Message).where(Message.conversation_id.in_(conv_ids)))
    db.execute(delete(Conversation).where(Conversation.guest_session_id == s.id, Conversation.user_id.is_(None)))
    db.delete(s)
    db.commit()
