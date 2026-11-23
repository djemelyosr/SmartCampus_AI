from datetime import datetime, timedelta, timezone

from conftest import register

PDF = b"%PDF-1.4\n%test\n"
TUNIS = timezone(timedelta(hours=1))


def _preinscribe(client, auth, program):
    client.put("/api/auth/me/profile", headers=auth, json={"consent_given": True})
    r = client.post("/api/preinscriptions", headers=auth, json={"program_id": program})
    assert r.status_code == 201, r.text


def test_health_and_auth_required(client):
    assert client.get("/health").json() == {"status": "ok"}
    for path in ("/api/qcm/current", "/api/appointments/me", "/api/documents"):
        assert client.get(path).status_code == 401


def test_qcm_requires_preinscription(client, auth):
    assert client.get("/api/qcm/current", headers=auth).status_code == 409


def test_qcm_full_flow_hides_answers_and_scores(client, auth, program):
    from app.services.qcm import BANK

    _preinscribe(client, auth, program)
    q = client.get("/api/qcm/current", headers=auth).json()
    assert len(q["questions"]) == 12 and not q["finished"]
    assert all("correct" not in x for x in q["questions"])  # the answer key must never leak
    assert client.get(f"/api/qcm/{q['id']}/results", headers=auth).status_code == 409

    answers = {i: item["correct"] for i, item in enumerate(BANK)}
    answers[0] = (BANK[0]["correct"] + 1) % 4  # one wrong -> 11/12
    url = f"/api/qcm/{q['id']}/answers"
    assert client.put(url, headers=auth, json={"answers": {0: 1}, "finish": True}).status_code == 422  # incomplete
    assert client.put(url, headers=auth, json={"answers": {0: 99}}).status_code == 422  # invalid option
    done = client.put(url, headers=auth, json={"answers": answers, "finish": True})
    assert done.status_code == 200 and done.json()["finished"]
    res = client.get(f"/api/qcm/{q['id']}/results", headers=auth).json()
    assert (res["good"], res["total"], res["pct"]) == (11, 12, 92)
    assert res["by_section"][0]["section"] == "Logique & algorithmique"
    assert client.put(url, headers=auth, json={"answers": answers}).status_code == 409  # frozen once finished


def test_qcm_is_private(client, auth, program):
    _preinscribe(client, auth, program)
    qid = client.get("/api/qcm/current", headers=auth).json()["id"]
    other = register(client, "other@example.com", "another-long-password")
    assert client.get(f"/api/qcm/{qid}/results", headers=other).status_code == 404
    assert client.put(f"/api/qcm/{qid}/answers", headers=other, json={"answers": {}}).status_code == 404


def _future_slots(client, auth):
    start = (datetime.now(timezone.utc) + timedelta(days=3)).date().isoformat()
    return client.get("/api/appointments/slots", headers=auth, params={"start": start, "days": 7}).json()


def test_appointment_booking_lifecycle(client, auth, program):
    slots = _future_slots(client, auth)
    assert slots and all(datetime.fromisoformat(s["slot"]).weekday() < 5 for s in slots)  # weekdays only
    slot = next(s["slot"] for s in slots if s["available"])
    assert client.post("/api/appointments", headers=auth, json={"slot": slot}).status_code == 409  # no pre-registration

    _preinscribe(client, auth, program)
    off_grid = datetime.fromisoformat(slot).replace(hour=3).isoformat()
    assert client.post("/api/appointments", headers=auth, json={"slot": off_grid}).status_code == 422
    booked = client.post("/api/appointments", headers=auth, json={"slot": slot})
    assert booked.status_code == 201 and booked.json()["status"] == "confirmed"
    aid = booked.json()["id"]

    day = [s for s in client.get("/api/appointments/slots", headers=auth, params={"start": slot[:10], "days": 1}).json() if s["slot"] == slot]
    assert day and not day[0]["available"]  # now taken
    assert client.post("/api/appointments", headers=auth, json={"slot": slot}).status_code == 409
    assert [a["id"] for a in client.get("/api/appointments/me", headers=auth).json()] == [aid]

    assert client.delete(f"/api/appointments/{aid}", headers=auth).json()["status"] == "cancelled"
    assert client.delete(f"/api/appointments/{aid}", headers=auth).status_code == 409
    assert client.post("/api/appointments", headers=auth, json={"slot": slot}).status_code == 201  # slot freed


def test_cannot_book_past_slot(client, auth, program):
    _preinscribe(client, auth, program)
    day = datetime.now(TUNIS) - timedelta(days=7)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    r = client.post("/api/appointments", headers=auth, json={"slot": day.replace(hour=9, minute=0, second=0, microsecond=0).isoformat()})
    assert r.status_code == 422


def test_second_candidate_cannot_take_booked_slot(client, auth, program):
    _preinscribe(client, auth, program)
    slot = next(s["slot"] for s in _future_slots(client, auth) if s["available"])
    assert client.post("/api/appointments", headers=auth, json={"slot": slot}).status_code == 201
    other = register(client, "second@example.com", "second-long-password")
    client.put("/api/auth/me/profile", headers=other, json={"consent_given": True})
    assert client.post("/api/preinscriptions", headers=other, json={"program_id": program}).status_code == 201
    assert client.post("/api/appointments", headers=other, json={"slot": slot}).status_code == 409


def test_document_upload_rules(client, auth, tmp_path):
    from app.core.config import settings

    ok = client.post("/api/documents", headers=auth, data={"kind": "Relevé de notes"}, files={"file": ("releve.pdf", PDF, "application/pdf")})
    assert ok.status_code == 201
    doc = ok.json()
    assert (doc["filename"], doc["status"], doc["size"]) == ("releve.pdf", "a_verifier", len(PDF))
    assert client.get(f"/api/documents/{doc['id']}/file", headers=auth).content == PDF
    assert len(client.get("/api/documents", headers=auth).json()) == 1

    assert client.post("/api/documents", headers=auth, files={"file": ("x.exe", b"MZ", "application/octet-stream")}).status_code == 415
    assert client.post("/api/documents", headers=auth, files={"file": ("fake.pdf", b"not a pdf", "application/pdf")}).status_code == 415
    assert client.post("/api/documents", headers=auth, data={"kind": "??"}, files={"file": ("a.pdf", PDF, "application/pdf")}).status_code == 422
    big = PDF + b"0" * settings.max_upload_bytes
    assert client.post("/api/documents", headers=auth, files={"file": ("big.pdf", big, "application/pdf")}).status_code == 413

    sneaky = client.post("/api/documents", headers=auth, files={"file": ("../../evil.pdf", PDF, "application/pdf")})
    assert sneaky.status_code == 201 and sneaky.json()["filename"] == "evil.pdf"
    stored = [p for p in (tmp_path / "uploads").rglob("*") if p.is_file()]
    assert stored and all(p.suffix == ".pdf" and tmp_path in p.parents for p in stored)


def test_documents_are_private(client, auth):
    d = client.post("/api/documents", headers=auth, files={"file": ("a.pdf", PDF, "application/pdf")}).json()
    snoop = register(client, "snoop@example.com", "snoop-long-password")
    assert client.get(f"/api/documents/{d['id']}/file", headers=snoop).status_code == 404
    assert client.get("/api/documents", headers=snoop).json() == []
