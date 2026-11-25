"""Optional existing-Derja LLM layer: rephrases the sourced reply, never at the expense of facts or official wording."""

import pytest

from app.agents import llm
from app.core.config import settings

ARABIZI = "chnowa chrouta el 9bol fil licence informatique ?"
MARK = "Message à réécrire :\n"


def _seed(client):
    from app.db.session import get_db
    from app.main import app as api
    from app.seed import seed_programs

    seed_programs(next(api.dependency_overrides[get_db]()))


def _chat(client, auth, text):
    cid = client.post("/api/conversations", headers=auth).json()["id"]
    r = client.post(f"/api/conversations/{cid}/messages", json={"content": text}, headers=auth)
    assert r.status_code == 200, r.text
    return cid, r.json()


@pytest.fixture()
def calls(monkeypatch):
    seen: list[list[dict]] = []
    monkeypatch.setattr(settings, "llm_enabled", True)

    def fake(messages):
        seen.append(messages)
        return "Yaatik essa7a ! " + messages[1]["content"].split(MARK, 1)[1]  # keeps every fact, adds a dialect touch

    monkeypatch.setattr(llm, "_post", fake)
    return seen


def test_disabled_by_default_keeps_deterministic_reply(client, auth):
    _seed(client)
    _, m = _chat(client, auth, ARABIZI)
    assert m["meta"]["llm"] == {"used": False} and not m["content"].startswith("Yaatik essa7a")


def test_faithful_rewrite_is_used_and_remembered(client, auth, calls):
    _seed(client)
    cid, m = _chat(client, auth, ARABIZI)
    assert m["meta"]["llm"]["used"] is True and m["content"].startswith("Yaatik essa7a !")
    assert m["meta"]["sources"] and len(calls) == 1
    assert "arabizi" in calls[0][0]["content"].lower() or "Arabizi" in calls[0][0]["content"]
    mem = client.get(f"/api/conversations/{cid}/memory", headers=auth).json()
    assert mem["turns"][-1]["t"].startswith("Yaatik essa7a")  # the session memory holds what the candidate saw


def test_unfaithful_rewrite_falls_back(client, auth, monkeypatch):
    _seed(client)
    monkeypatch.setattr(settings, "llm_enabled", True)
    monkeypatch.setattr(llm, "_post", lambda messages: "نص عربي بلا أي معلومة")  # wrong script for Arabizi, facts lost
    _, m = _chat(client, auth, ARABIZI)
    assert m["meta"]["llm"]["used"] is False and m["meta"]["llm"]["fallback"] in {"numbers_changed", "wrong_script"}
    assert "9bol" in m["content"].lower() or "chrouta" in m["content"].lower()


def test_llm_failure_never_breaks_the_conversation(client, auth, monkeypatch):
    _seed(client)
    monkeypatch.setattr(settings, "llm_enabled", True)

    def boom(messages):
        raise TimeoutError("model server down")

    monkeypatch.setattr(llm, "_post", boom)
    _, m = _chat(client, auth, ARABIZI)
    assert m["meta"]["llm"]["fallback"] == "unavailable" and m["content"] and m["meta"]["sources"]


def test_official_wording_and_french_are_never_sent_to_the_model(client, auth, calls):
    _seed(client)
    _, handoff = _chat(client, auth, "nheb na3ref maqboul walla le")
    assert handoff["meta"]["action"] == "human_handoff" and handoff["meta"]["llm"]["skipped"]
    _, french = _chat(client, auth, "Bonjour, quelles sont les conditions d’accès à la licence en informatique ?")
    assert french["meta"]["language"] == "fr" and french["meta"]["llm"]["skipped"]
    assert calls == []


def test_faithful_checks():
    orig = "• Licence en informatique (IIT) — compatibilité 82 % · durée : 3 an(s)"
    ok = "• Licence en informatique (IIT) — compatibilité 82 % · modda : 3 an(s)"
    assert llm.faithful(orig, ok, "arabizi", ["Licence en informatique"]) is None
    assert llm.faithful(orig, ok.replace("82", "95"), "arabizi", []) == "numbers_changed"
    assert llm.faithful(orig, ok.replace("Licence en informatique", "Licence info"), "arabizi", ["Licence en informatique"]) == "formation_name_changed"
    assert llm.faithful(orig, "", "arabizi", []) == "empty"
    assert llm.faithful(orig, ok * 20, "arabizi", []) == "too_long"
