"""Visitor sessions: automatic creation, ownership, limits, expiry, and attaching them to a candidate account."""

from datetime import timedelta

import pytest

from conftest import make_user

H = "X-Guest-Session"


def _start(client, token=None):
    r = client.post("/api/conversations", headers={H: token} if token else {})
    assert r.status_code == 201, r.text
    return r


def _say(client, conv_id, token, text="Bonjour, je cherche une licence"):
    return client.post(f"/api/conversations/{conv_id}/messages", headers={H: token}, json={"content": text})


def test_visitor_session_is_created_automatically(client):
    r = _start(client)
    body, token = r.json(), r.headers[H]
    assert body["guest_session"]["token"] == token and len(body["guest_session"]["id"]) == 32
    assert body["guest_session"]["expires_at"] and body["guest_session"]["messages_left"] > 0
    # the visitor chats with the token
    reply = _say(client, body["id"], token)
    assert reply.status_code == 200 and reply.json()["role"] == "assistant"
    conv = client.get(f"/api/conversations/{body['id']}", headers={H: token}).json()
    assert [m["role"] for m in conv["messages"]] == ["user", "assistant"]
    info = client.get("/api/guest/session", headers={H: token}).json()
    assert info["messages_used"] == 1 and info["conversation_ids"] == [body["id"]]
    # a second conversation in the same session does not create a new session (no token returned)
    again = _start(client, token).json()
    assert again["guest_session"]["id"] == body["guest_session"]["id"] and again["guest_session"]["token"] is None


def test_only_the_token_holder_can_read_or_write(client, db):
    a = _start(client)
    b = _start(client)
    conv_a, tok_a, tok_b = a.json()["id"], a.headers[H], b.headers[H]
    assert _say(client, conv_a, tok_b).status_code == 404  # another visitor
    assert client.get(f"/api/conversations/{conv_a}").status_code == 404  # no token
    forged = tok_a.split(".")[0] + ".not-the-secret"
    assert client.get(f"/api/conversations/{conv_a}", headers={H: forged}).status_code == 401
    cand = make_user(db, client, "candidate", "c@example.com")
    assert client.get(f"/api/conversations/{conv_a}", headers=cand).status_code == 404  # an account is not the visitor
    # the secret is never stored in clear
    from app.models.models import GuestSession

    s = db.get(GuestSession, tok_a.split(".")[0])
    assert s.secret_hash != tok_a.split(".")[1] and len(s.secret_hash) == 64


def test_signed_in_users_keep_their_own_conversations(client, db):
    cand = make_user(db, client, "candidate", "user@example.com")
    r = client.post("/api/conversations", headers=cand)
    assert r.status_code == 201 and r.json()["guest_session"] is None and H not in r.headers
    assert client.post(f"/api/conversations/{r.json()['id']}/messages", headers=cand, json={"content": "Salut"}).status_code == 200
    assert [c["id"] for c in client.get("/api/conversations", headers=cand).json()] == [r.json()["id"]]


def test_limits(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "guest_messages_per_minute", 2)
    monkeypatch.setattr(settings, "guest_max_messages", 3)
    monkeypatch.setattr(settings, "guest_max_conversations", 2)
    monkeypatch.setattr(settings, "guest_message_max_chars", 50)
    r = _start(client)
    conv, tok = r.json()["id"], r.headers[H]
    assert _say(client, conv, tok, "x" * 51).status_code == 422
    assert _say(client, conv, tok, "   ").status_code == 422
    assert _say(client, conv, tok).status_code == 200
    assert _say(client, conv, tok).status_code == 200
    assert _say(client, conv, tok).status_code == 429  # 2 per minute
    monkeypatch.setattr(settings, "guest_messages_per_minute", 10)
    assert _say(client, conv, tok).status_code == 200
    capped = _say(client, conv, tok)
    assert capped.status_code == 429 and "create an account" in capped.json()["detail"]
    _start(client, tok)
    assert client.post("/api/conversations", headers={H: tok}).status_code == 429  # 2 conversations max


def test_sessions_per_network_address(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "guest_sessions_per_hour_per_client", 2)
    _start(client), _start(client)
    assert client.post("/api/conversations").status_code == 429
    assert client.post("/api/guest/sessions").status_code == 429


def test_expiry_and_cleanup(client, db, monkeypatch):
    from app.core.config import settings
    from app.models.models import Conversation, GuestSession, GuestStatus
    from app.services import guest

    r = _start(client)
    conv, tok = r.json()["id"], r.headers[H]
    _say(client, conv, tok)
    sid = tok.split(".")[0]
    s = db.get(GuestSession, sid)
    # sliding expiry, never beyond the maximum lifetime
    assert guest.aware(s.expires_at) - guest.aware(s.created_at) <= timedelta(minutes=settings.guest_idle_minutes, seconds=5)

    s.expires_at = guest.now() - timedelta(minutes=1)
    db.commit()
    expired = _say(client, conv, tok)
    assert expired.status_code == 401 and "expired" in expired.json()["detail"]
    db.expire_all()
    assert db.get(GuestSession, sid).status == GuestStatus.expired

    # clean-up deletes expired visitor sessions (and their messages) after the retention delay
    monkeypatch.setattr(settings, "guest_retention_hours", 0)
    assert guest.purge_expired(db)["deleted"] == 1
    db.expire_all()
    assert db.get(GuestSession, sid) is None and db.get(Conversation, conv) is None


def test_purge_marks_stale_sessions(client, db):
    from app.models.models import GuestSession, GuestStatus
    from app.services import guest

    tok = _start(client).headers[H]
    s = db.get(GuestSession, tok.split(".")[0])
    s.expires_at = guest.now() - timedelta(seconds=1)
    db.commit()
    assert guest.purge_expired(db) == {"expired": 1, "deleted": 0}  # kept until the retention delay
    db.expire_all()
    assert db.get(GuestSession, s.id).status == GuestStatus.expired


def test_claim_requires_consent_and_ownership(client, db):
    r = _start(client)
    conv, tok = r.json()["id"], r.headers[H]
    _say(client, conv, tok, "Je veux faire de l’informatique")
    cand = make_user(db, client, "candidate", "fatma@example.com")
    staff = make_user(db, client, "interviewer", "staff@example.com")

    preview = client.get("/api/guest/claim/preview", headers={**cand, H: tok})
    assert preview.status_code == 200
    p = preview.json()
    assert p["conversations"] == 1 and p["messages"] == 2 and p["first_message"].startswith("Je veux") and p["consent_text"]

    assert client.post("/api/guest/claim", headers=cand, json={"consent": False, "guest_token": tok}).status_code == 400
    assert client.post("/api/guest/claim", headers=cand, json={"consent": True}).status_code == 400  # no token
    assert client.post("/api/guest/claim", headers=cand, json={"consent": True, "guest_token": tok.split(".")[0] + ".bad"}).status_code == 401
    assert client.post("/api/guest/claim", headers=staff, json={"consent": True, "guest_token": tok}).status_code == 403
    assert client.post("/api/guest/claim", json={"consent": True, "guest_token": tok}).status_code == 401

    ok = client.post("/api/guest/claim", headers=cand, json={"consent": True, "guest_token": tok})
    assert ok.status_code == 200 and ok.json()["attached_conversation_ids"] == [conv] and ok.json()["messages"] == 2
    # the conversation now belongs to the account, with its history
    mine = client.get("/api/conversations", headers=cand).json()
    assert [c["id"] for c in mine] == [conv] and len(mine[0]["messages"]) == 2
    assert client.post(f"/api/conversations/{conv}/messages", headers=cand, json={"content": "Merci"}).status_code == 200
    # the visitor token cannot be used any more (and cannot be claimed twice)
    assert _say(client, conv, tok).status_code in (404, 409)
    again = client.post("/api/guest/claim", headers=make_user(db, client, "candidate", "other@example.com"), json={"consent": True, "guest_token": tok})
    assert again.status_code == 409
    assert client.delete("/api/guest/session", headers={H: tok}).status_code == 409

    from app.models.models import GuestSession, GuestStatus

    s = db.get(GuestSession, tok.split(".")[0])
    db.refresh(s)
    assert s.status == GuestStatus.claimed and s.claim_consent_at is not None
    # claimed conversations survive the clean-up of visitor sessions
    from app.services import guest

    s.expires_at = guest.now() - timedelta(days=10)
    db.commit()
    guest.purge_expired(db)
    assert len(client.get("/api/conversations", headers=cand).json()) == 1


def test_expired_session_cannot_be_claimed(client, db):
    from app.models.models import GuestSession
    from app.services import guest

    tok = _start(client).headers[H]
    s = db.get(GuestSession, tok.split(".")[0])
    s.expires_at = guest.now() - timedelta(minutes=1)
    db.commit()
    cand = make_user(db, client, "candidate", "late@example.com")
    assert client.post("/api/guest/claim", headers=cand, json={"consent": True, "guest_token": tok}).status_code == 401


def test_visitor_can_discard_the_session(client, db):
    from app.models.models import Conversation

    r = _start(client)
    conv, tok = r.json()["id"], r.headers[H]
    _say(client, conv, tok)
    assert client.delete("/api/guest/session", headers={H: tok}).status_code == 204
    db.expire_all()
    assert db.get(Conversation, conv) is None
    assert client.get("/api/guest/session", headers={H: tok}).status_code == 401
    assert client.get("/api/guest/limits").json()["max_messages"] > 0
