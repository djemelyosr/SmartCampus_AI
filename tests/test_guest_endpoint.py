from app.api.routes import conversations as conv_routes
from app.core.config import settings
from app.db.session import get_db
from app.main import app as api
from app.models.models import Conversation, Message
from app.seed import seed_programs
from app.seed_catalog import seed_catalog

URL = "/api/conversations/guest/messages"


def _seed():
    db = next(api.dependency_overrides[get_db]())
    seed_programs(db)
    seed_catalog(db)
    return db


def ask(client, text, state=None):
    return client.post(URL, json={"content": text, "state": state})


def test_visitor_chats_without_account_and_nothing_is_stored(client):
    db = _seed()
    r = ask(client, "Quelles sont les conditions d'admission pour la licence en informatique ?")
    assert r.status_code == 200  # "guest" is not read as a conversation id
    body = r.json()
    assert body["content"] and body["meta"]["action"] and body["state"]["memory"]["turns"]
    assert db.query(Conversation).count() == 0 and db.query(Message).count() == 0


def test_follow_up_is_understood_from_the_state_returned_to_the_browser(client):
    _seed()
    first = ask(client, "Quelles sont les conditions d'admission pour la licence en informatique ?").json()
    focus = first["state"]["memory"]["last_programs"]
    assert focus  # the formation just discussed is what "it" will mean
    second = ask(client, "Et la durée ?", first["state"]).json()
    assert second["meta"]["memory"]["new"] is False
    assert "Licence en informatique" in " ".join(second["meta"]["sources"])
    assert second["state"]["memory"]["last_programs"] == focus
    # without the state the same question has nothing to refer to
    assert ask(client, "Et la durée ?").json()["meta"]["sources"] != second["meta"]["sources"]


def test_visitor_is_asked_to_create_an_account_for_a_preinscription(client):
    _seed()
    r = ask(client, "Je veux faire la préinscription à la licence en informatique").json()
    assert r["meta"]["action"] == "need_account"
    assert "compte" in r["content"].lower()


def test_tampered_or_oversized_state_is_harmless(client):
    _seed()
    ok = ask(client, "Bonjour", {"profile": "x", "memory": 5, "language": {"a": 1}})
    assert ok.status_code == 200 and ok.json()["content"]
    big = ask(client, "Bonjour", {"memory": {"turns": [{"r": "user", "t": "x" * 100}] * 400}})
    assert big.status_code in (200, 413)
    huge = ask(client, "Bonjour", {"blob": "x" * (settings.guest_max_state_bytes + 10)})
    assert huge.status_code == 413
    assert client.post(URL, json={"content": ""}).status_code == 422
    assert client.post(URL, json={"content": "x" * 2001}).status_code == 422


def test_visitor_messages_are_rate_limited(client, monkeypatch):
    _seed()
    conv_routes._guest_hits.clear()
    monkeypatch.setattr(settings, "guest_messages_per_minute", 3)
    codes = [ask(client, "Bonjour").status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200] and codes[3:] == [429, 429]
    conv_routes._guest_hits.clear()


def test_signed_in_user_still_has_a_private_conversation(client, auth):
    _seed()
    cid = client.post("/api/conversations", headers=auth).json()["id"]
    assert client.post(f"/api/conversations/{cid}/messages", json={"content": "Bonjour"}, headers=auth).status_code == 200
    assert client.post(f"/api/conversations/{cid}/messages", json={"content": "Bonjour"}).status_code == 401  # no token, no access



# --- the visitor's working memory expires like an account's one ---------------------------------------------------------------
FIRST = "Quelles sont les conditions d'admission pour la licence en informatique ?"


def _first(client):
    _seed()
    return ask(client, FIRST).json()


def _age(state, minutes):
    state["memory"]["seen"] -= minutes * 60
    state["memory"]["born"] -= minutes * 60


def test_visitor_memory_is_stamped_and_reports_its_remaining_life(client):
    first = _first(client)
    mem = first["state"]["memory"]
    assert mem["born"] <= mem["seen"]
    assert 0 < first["meta"]["memory"]["expires_in_seconds"] <= settings.session_ttl_minutes * 60


def test_visitor_memory_expires_after_idle_time(client):
    first = _first(client)
    _age(first["state"], settings.session_ttl_minutes + 1)
    second = ask(client, "Et la durée ?", first["state"]).json()
    assert second["meta"]["memory"]["new"] is True  # forgotten: "it" no longer points to the previous formation
    assert [t["t"] for t in second["state"]["memory"]["turns"] if t["r"] == "user"] == ["Et la durée ?"]


def test_visitor_memory_has_an_absolute_lifetime(client):
    first = _first(client)
    first["state"]["memory"]["born"] -= (settings.session_max_age_minutes + 1) * 60  # kept alive by activity, but too old
    second = ask(client, "Et la durée ?", first["state"]).json()
    assert second["meta"]["memory"]["new"] is True
    assert second["state"]["memory"]["born"] > first["state"]["memory"]["born"]


def test_visitor_memory_survives_while_active_and_slides_the_idle_expiry(client):
    first = _first(client)
    _age(first["state"], settings.session_ttl_minutes - 1)  # almost idle-expired, still alive
    second = ask(client, "Et la durée ?", first["state"]).json()
    assert second["meta"]["memory"]["new"] is False
    assert second["state"]["memory"]["seen"] > first["state"]["memory"]["seen"]


def test_unstamped_or_tampered_visitor_memory_is_dropped(client):
    first = _first(client)
    mem = first["state"]["memory"]
    unstamped = {**first["state"], "memory": {k: v for k, v in mem.items() if k not in ("born", "seen")}}
    assert ask(client, "Et la durée ?", unstamped).json()["meta"]["memory"]["new"] is True
    future = {**first["state"], "memory": {**mem, "seen": mem["seen"] + 10 * 24 * 3600}}
    assert ask(client, "Et la durée ?", future).json()["meta"]["memory"]["new"] is True
    junk = {**first["state"], "memory": {**mem, "born": "yesterday"}}
    assert ask(client, "Et la durée ?", junk).status_code == 200
