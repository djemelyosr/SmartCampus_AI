from app.agents.language import detect_language


def test_language_detection():
    assert detect_language("Bonjour, je voudrais des informations sur la licence") == "fr"
    assert detect_language("nheb net3alem informatique, 3andi bac math") == "arabizi"
    assert detect_language("نحب نقرا إعلامية و رياضيات") == "tn"


def _chat(client, auth, cid, text):
    r = client.post(f"/api/conversations/{cid}/messages", json={"content": text}, headers=auth)
    assert r.status_code == 200, r.text
    return r.json()


def _seed(client):
    from app.api.deps import current_user  # noqa: F401
    from app.db.session import get_db
    from app.main import app as api
    from app.seed import seed_programs

    db = next(api.dependency_overrides[get_db]())
    seed_programs(db)


def test_agent_builds_profile_then_shortlists_with_sources(client, auth):
    _seed(client)
    cid = client.post("/api/conversations", headers=auth).json()["id"]
    m1 = _chat(client, auth, cid, "J’aime les maths et l’informatique")
    assert m1["meta"]["agent"] == "supervisor" and m1["meta"]["action"].startswith("ask_")
    m2 = _chat(client, auth, cid, "Je veux devenir ingénieur logiciel, bac maths, j’aime les projets pratiques")
    assert m2["meta"]["action"] == "shortlist"
    assert 1 <= len(m2["meta"]["shortlist"]) <= 3 and m2["meta"]["sources"]
    prof = client.get("/api/auth/me/profile", headers=auth).json()
    assert "maths" in prof["favorite_subjects"] and prof["consent_given"] is False


def test_agent_answers_in_arabizi_and_uses_rag(client, auth):
    _seed(client)
    cid = client.post("/api/conversations", headers=auth).json()["id"]
    m = _chat(client, auth, cid, "chnowa chrouta el 9bol fil licence informatique ?")
    assert m["meta"]["language"] == "arabizi"
    assert m["meta"]["action"] == "rag_conditions" and m["meta"]["sources"]


def test_agent_never_decides_admission_and_hands_off(client, auth):
    cid = client.post("/api/conversations", headers=auth).json()["id"]
    m = _chat(client, auth, cid, "Est-ce que je suis admis ?")
    assert m["meta"]["handoff"] is True and m["meta"]["action"] == "human_handoff"


def test_preinscription_requires_consent(client, auth):
    _seed(client)
    cid = client.post("/api/conversations", headers=auth).json()["id"]
    m = _chat(client, auth, cid, "Je veux faire la préinscription à la licence en informatique")
    assert m["meta"]["action"] == "need_consent"
    assert client.get("/api/preinscriptions", headers=auth).json() == []
    client.put("/api/auth/me/profile", json={"consent_given": True}, headers=auth)
    m = _chat(client, auth, cid, "Je veux faire la préinscription à la licence en informatique")
    assert m["meta"]["action"] == "preinscription_created"
    assert len(client.get("/api/preinscriptions", headers=auth).json()) == 1
