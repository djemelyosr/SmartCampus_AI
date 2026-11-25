"""Session memory: temporary, redacted, bounded and expiring working memory of a conversation."""

from datetime import timedelta

from sqlalchemy import select

from app.core.config import settings
from app.models.models import SessionMemory
from app.services import session_memory as sm


def _db():
    from app.db.session import get_db
    from app.main import app as api

    return next(api.dependency_overrides[get_db]())


def _seed(client):
    from app.seed import seed_programs

    seed_programs(_db())


def _chat(client, auth, cid, text):
    r = client.post(f"/api/conversations/{cid}/messages", json={"content": text}, headers=auth)
    assert r.status_code == 200, r.text
    return r.json()


def _conv(client, auth) -> int:
    return client.post("/api/conversations", headers=auth).json()["id"]


# --- what is kept (pure functions) -------------------------------------------------------------------------------------
def test_redact_masks_email_and_phone_but_not_years():
    t = sm.redact("écrivez à ali.ben@example.com ou appelez le 22 345 678, rentrée 2026-2027")
    assert "[email]" in t and "[numéro]" in t and "example.com" not in t and "345" not in t
    assert "2026-2027" in t


def test_clip_limits_length():
    assert len(sm.clip("a" * 5000)) <= settings.session_max_chars


def test_bound_keeps_last_turns_and_programs_and_size(monkeypatch):
    monkeypatch.setattr(settings, "session_max_turns", 2)
    data = sm.empty()
    for i in range(20):
        sm.record_turn(data, "user", f"message {i}")
    data["last_programs"] = [1, 2, 3, 4, 5]
    sm.bound(data)
    assert len(data["turns"]) == 4 and data["turns"][-1]["t"] == "message 19"
    assert data["last_programs"] == [1, 2, 3]
    monkeypatch.setattr(settings, "session_max_bytes", 150)
    assert len(sm.bound(data)["turns"]) < 4


# --- follow-up questions understood from memory --------------------------------------------------------------------------
def test_followup_uses_the_formation_just_discussed(client, auth):
    _seed(client)
    cid = _conv(client, auth)
    first = _chat(client, auth, cid, "chnowa chrouta el 9bol fil licence informatique ?")
    assert first["meta"]["action"] == "rag_conditions" and first["meta"]["memory"]["new"] is True
    again = _chat(client, auth, cid, "et les débouchés ?")  # no formation named: it comes from memory
    assert again["meta"]["action"] == "rag_debouches"
    assert again["meta"]["sources"] == first["meta"]["sources"][: len(again["meta"]["sources"])]
    assert again["meta"]["memory"]["new"] is False


def test_bare_answer_resumes_the_interrupted_request(client, auth):
    _seed(client)
    cid = _conv(client, auth)
    assert _chat(client, auth, cid, "Je veux m’inscrire")["meta"]["action"] == "ask_program"
    m = _chat(client, auth, cid, "la licence en informatique")
    assert m["meta"]["action"] == "need_consent" and m["meta"]["memory"]["resumed"] == "preinscription"
    client.put("/api/auth/me/profile", json={"consent_given": True}, headers=auth)
    m = _chat(client, auth, cid, "c’est fait")  # nothing named: the pending formation is used
    assert m["meta"]["action"] == "preinscription_created"
    assert len(client.get("/api/preinscriptions", headers=auth).json()) == 1


def test_long_message_is_a_new_request_not_a_resume(client, auth):
    _seed(client)
    cid = _conv(client, auth)
    _chat(client, auth, cid, "Je veux m’inscrire")
    m = _chat(client, auth, cid, "Quelles sont les conditions d’accès à la licence en informatique pour un bachelier ?")
    assert m["meta"]["action"] == "rag_conditions" and not m["meta"]["memory"]["resumed"]


# --- inspection, privacy, limits, expiry -----------------------------------------------------------------------------------
def test_memory_endpoint_is_redacted_and_bounded(client, auth, monkeypatch):
    monkeypatch.setattr(settings, "session_max_turns", 2)
    cid = _conv(client, auth)
    assert client.get(f"/api/conversations/{cid}/memory", headers=auth).json()["active"] is False
    _chat(client, auth, cid, "Mon email est ali.ben@example.com et mon numéro 22 345 678, j’aime les maths")
    for i in range(5):
        _chat(client, auth, cid, f"j’aime la physique {i}")
    mem = client.get(f"/api/conversations/{cid}/memory", headers=auth).json()
    assert mem["active"] and 0 < mem["expires_in_seconds"] <= settings.session_ttl_minutes * 60
    assert len(mem["turns"]) <= 4 and mem["limits"]["max_turns"] == 2
    assert "example.com" not in str(mem) and "345" not in str(mem)
    first = client.post("/api/conversations", headers=auth).json()["id"]
    _chat(client, auth, first, "Mon email est ali.ben@example.com")
    assert "[email]" in str(client.get(f"/api/conversations/{first}/memory", headers=auth).json()["turns"])


def test_expired_memory_is_ignored_then_restarted(client, auth):
    _seed(client)
    cid = _conv(client, auth)
    _chat(client, auth, cid, "chnowa chrouta el 9bol fil licence informatique ?")
    db = _db()
    row = db.scalar(select(SessionMemory).where(SessionMemory.conversation_id == cid))
    assert row.data["last_programs"]
    row.expires_at = sm.now() - timedelta(seconds=1)
    db.commit()
    assert client.get(f"/api/conversations/{cid}/memory", headers=auth).json()["active"] is False
    m = _chat(client, auth, cid, "et les débouchés ?")  # memory gone: it no longer knows which formation
    assert m["meta"]["memory"]["new"] is True
    assert m["meta"]["action"] != "rag_debouches" or m["meta"]["sources"] != []  # never invents an answer


def test_absolute_lifetime_is_not_extended_by_activity(client, auth):
    cid = _conv(client, auth)
    _chat(client, auth, cid, "j’aime les maths")
    db = _db()
    row = db.scalar(select(SessionMemory).where(SessionMemory.conversation_id == cid))
    row.created_at = sm.now() - timedelta(minutes=settings.session_max_age_minutes + 1)
    db.commit()
    assert _chat(client, auth, cid, "j’aime la physique")["meta"]["memory"]["new"] is True


def test_forget_and_isolation_between_users(client, auth):
    cid = _conv(client, auth)
    _chat(client, auth, cid, "j’aime les maths")
    other = client.post("/api/auth/register", json={"email": "autre@example.com", "password": "a-long-test-password", "full_name": "Autre"})
    assert other.status_code == 201
    tok = client.post("/api/auth/login", data={"username": "autre@example.com", "password": "a-long-test-password"}).json()["access_token"]
    stranger = {"Authorization": f"Bearer {tok}"}
    assert client.get(f"/api/conversations/{cid}/memory", headers=stranger).status_code == 404
    assert client.delete(f"/api/conversations/{cid}/memory", headers=stranger).status_code == 404
    assert client.delete(f"/api/conversations/{cid}/memory", headers=auth).status_code == 204
    assert client.get(f"/api/conversations/{cid}/memory", headers=auth).json()["active"] is False
    # the durable record is untouched: the profile built so far survives
    assert "maths" in client.get("/api/auth/me/profile", headers=auth).json()["favorite_subjects"]


def test_purge_removes_only_expired_memories(client, auth):
    a, b = _conv(client, auth), _conv(client, auth)
    _chat(client, auth, a, "j’aime les maths")
    _chat(client, auth, b, "j’aime la physique")
    db = _db()
    row = db.scalar(select(SessionMemory).where(SessionMemory.conversation_id == a))
    row.expires_at = sm.now() - timedelta(minutes=1)
    db.commit()
    assert sm.purge_expired(db) == 1
    left = db.scalars(select(SessionMemory)).all()
    assert [r.conversation_id for r in left] == [b]
