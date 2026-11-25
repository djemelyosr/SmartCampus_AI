"""Temporary working memory of a conversation (the "session").

Why: the agent must understand follow-up questions ("et les débouchés ?", "je veux m'inscrire") without asking again
what the candidate already said. The durable record stays where it was (Message history, CandidateProfile, the slot
profile in Conversation.state used by interviews and statistics). This module only holds what is useful *right now*:

    turns          the last few messages, redacted and clipped (emails / phone numbers never stored)
    last_programs  formations discussed in the last answer (what "it / this one" refers to)
    last_intent    last request understood, last_action = what the agent answered
    pending        the question the agent just asked, so a bare answer resumes the interrupted request

Limits (see Settings): number of turns, characters per message, serialised size, an idle TTL that is extended at every
message, and an absolute lifetime. An expired memory is reset on next use, purged in the background and on startup.
"""

import json
import re
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Conversation, SessionMemory

VERSION = 1
MAX_PROGRAMS = 3
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_NUMBER = re.compile(r"(?<!\w)\+?\d[\d .\-]{5,}\d(?!\w)")
_YEARS = re.compile(r"(?:19|20)\d{2}\s?[-–/]\s?(?:19|20)?\d{2}")  # school year "2026-2027" is not personal data
_last_purge = 0.0


def now() -> datetime:
    return datetime.now(timezone.utc)


def aware(dt: datetime) -> datetime:
    """SQLite returns naive datetimes: everything is stored and compared as UTC."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def empty() -> dict:
    return {"v": VERSION, "turns": [], "last_programs": [], "last_intent": None, "last_action": None, "pending": None}


# --- what is kept ----------------------------------------------------------------------------------------------------
def _mask_number(m: re.Match) -> str:
    if _YEARS.fullmatch(m.group()):
        return m.group()
    return "[numéro]" if sum(c.isdigit() for c in m.group()) >= 7 else m.group()  # phone, CIN... but not "2026-2027"


def redact(text: str) -> str:
    return _NUMBER.sub(_mask_number, _EMAIL.sub("[email]", text))


def clip(text: str, limit: int | None = None) -> str:
    limit = limit or settings.session_max_chars
    t = " ".join(redact(text or "").split())
    return t if len(t) <= limit else t[: limit - 1].rstrip() + "…"


def record_turn(data: dict, role: str, text: str, action: str | None = None) -> None:
    turn = {"r": role, "t": clip(text)}
    if action:
        turn["a"] = action
    data["turns"].append(turn)


def bound(data: dict) -> dict:
    """Enforce every limit in place (also on a memory written under older, larger limits)."""
    for key, value in empty().items():
        data.setdefault(key, value)
    data["turns"] = [{**t, "t": clip(t.get("t", ""))} for t in data["turns"][-2 * settings.session_max_turns:]]
    data["last_programs"] = [int(i) for i in data["last_programs"]][:MAX_PROGRAMS]
    while data["turns"] and len(json.dumps(data, ensure_ascii=False).encode()) > settings.session_max_bytes:
        data["turns"].pop(0)  # oldest first
    return data


# --- lifecycle -------------------------------------------------------------------------------------------------------
def _expired(row: SessionMemory, at: datetime) -> bool:
    return aware(row.expires_at) <= at or aware(row.created_at) + timedelta(minutes=settings.session_max_age_minutes) <= at


def load(db: Session, conv: Conversation) -> tuple[SessionMemory, dict, bool]:
    """Working memory of the conversation. `fresh` = new or expired: it starts again from nothing."""
    maybe_purge(db)
    at = now()
    row = db.scalar(select(SessionMemory).where(SessionMemory.conversation_id == conv.id))
    fresh = False
    if row is None:
        row = SessionMemory(conversation_id=conv.id, user_id=conv.user_id, data=empty(), created_at=at, updated_at=at,
                            expires_at=at + timedelta(minutes=settings.session_ttl_minutes))
        db.add(row)
        db.flush()
        fresh = True
    elif _expired(row, at):
        row.data, row.created_at, fresh = empty(), at, True
    return row, bound(dict(row.data or {})), fresh


def save(row: SessionMemory, data: dict) -> None:
    """Persist the bounded memory and slide the idle expiry (never beyond the absolute lifetime)."""
    at = now()
    row.data = bound(data)
    row.updated_at = at
    row.expires_at = min(at + timedelta(minutes=settings.session_ttl_minutes),
                         aware(row.created_at) + timedelta(minutes=settings.session_max_age_minutes))


def peek(db: Session, conv_id: int) -> SessionMemory | None:
    """The live memory of a conversation, or None (never created, expired or forgotten). Read-only."""
    row = db.scalar(select(SessionMemory).where(SessionMemory.conversation_id == conv_id))
    return None if row is None or _expired(row, now()) else row


def forget(db: Session, conv_id: int) -> bool:
    return bool(db.execute(delete(SessionMemory).where(SessionMemory.conversation_id == conv_id)).rowcount)


def purge_expired(db: Session, commit: bool = True) -> int:
    at = now()
    oldest = at - timedelta(minutes=settings.session_max_age_minutes)
    n = db.execute(delete(SessionMemory).where(or_(SessionMemory.expires_at <= at, SessionMemory.created_at <= oldest))).rowcount or 0
    if commit:
        db.commit()
    return n


def maybe_purge(db: Session) -> None:
    """Opportunistic clean-up inside a request (at most once per interval); the caller's commit applies it."""
    global _last_purge
    t = time.monotonic()
    if t - _last_purge >= settings.session_purge_interval_seconds:
        _last_purge = t
        purge_expired(db, commit=False)


# --- visitor without account -----------------------------------------------------------------------------------------------
# Nothing is stored server-side: the memory travels with the browser, stamped with when it was started ("born") and last
# used ("seen"), and the same two limits apply (idle TTL, absolute lifetime). The browser sends the state back, so these
# stamps are untrusted: a visitor can at most keep their *own* context longer, never read or affect another visitor's.
def guest_expired(data: dict, at: datetime | None = None) -> bool:
    """True when a visitor's memory must start again: idle too long, too old, unstamped (or tampered) with content."""
    if not data:
        return False
    try:
        t = (at or now()).timestamp()
        born, seen = float(data["born"]), float(data["seen"])
    except (KeyError, TypeError, ValueError):
        return True
    return seen + settings.session_ttl_minutes * 60 <= t or born + settings.session_max_age_minutes * 60 <= t or seen < born or seen > t + 60


def guest_stamp(data: dict) -> dict:
    """Slide the idle expiry (the absolute lifetime keeps counting from `born`)."""
    t = now().timestamp()
    data["born"] = min(float(data.get("born") or t), t)
    data["seen"] = t
    return data


def guest_left(data: dict) -> int:
    """Seconds before a visitor's memory expires (0 when it has no stamps yet)."""
    try:
        end = min(float(data["seen"]) + settings.session_ttl_minutes * 60, float(data["born"]) + settings.session_max_age_minutes * 60)
    except (KeyError, TypeError, ValueError):
        return 0
    return max(0, int(end - now().timestamp()))


def describe(row: SessionMemory) -> dict:
    """What the candidate may inspect (GET /conversations/{id}/memory)."""
    data = bound(dict(row.data or {}))
    left = max(0, int((aware(row.expires_at) - now()).total_seconds()))
    return {
        "active": True, "expires_at": aware(row.expires_at), "expires_in_seconds": left, "turns": data["turns"],
        "context": {k: data[k] for k in ("last_programs", "last_intent", "last_action", "pending")},
        "limits": {"ttl_minutes": settings.session_ttl_minutes, "max_age_minutes": settings.session_max_age_minutes,
                   "max_turns": settings.session_max_turns, "max_chars_per_message": settings.session_max_chars},
    }
