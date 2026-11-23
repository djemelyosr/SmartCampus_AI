from datetime import datetime

from conftest import register

PDF = b"%PDF-1.4\n%test\n"


def _db(client):
    from app.db.session import get_db
    from app.main import app as api

    return next(api.dependency_overrides[get_db]())


def test_seed_programs_is_idempotent_and_listed(client):
    from app.seed import PROGRAMS, seed_programs

    db = _db(client)
    assert seed_programs(db) == len(PROGRAMS)
    assert seed_programs(db) == 0  # second run adds nothing
    names = {p["name"] for p in client.get("/api/programs").json()}
    assert {"Licence en informatique", "Cycle préparatoire", "Parcours en gestion"} <= names


def test_qcm_results_expose_finish_time(client):
    from app.seed import seed_programs
    from app.services.qcm import BANK

    seed_programs(_db(client))
    auth = register(client, "dates@example.com", "dates-long-password")
    pid = client.get("/api/programs").json()[0]["id"]
    client.put("/api/auth/me/profile", headers=auth, json={"consent_given": True})
    assert client.post("/api/preinscriptions", headers=auth, json={"program_id": pid}).status_code == 201
    q = client.get("/api/qcm/current", headers=auth).json()
    answers = {i: it["correct"] for i, it in enumerate(BANK)}
    client.put(f"/api/qcm/{q['id']}/answers", headers=auth, json={"answers": answers, "finish": True})
    res = client.get(f"/api/qcm/{q['id']}/results", headers=auth).json()
    assert res["pct"] == 100
    assert datetime.fromisoformat(res["finished_at"]).tzinfo is not None


def test_document_has_upload_date(client):
    auth = register(client, "docdate@example.com", "docdate-long-password")
    d = client.post("/api/documents", headers=auth, files={"file": ("a.pdf", PDF, "application/pdf")}).json()
    assert d["created_at"] is not None
    assert client.get("/api/documents", headers=auth).json()[0]["created_at"] is not None
