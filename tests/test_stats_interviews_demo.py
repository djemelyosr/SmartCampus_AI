"""Statistics and interview files on the demo data, demo accounts, schema check."""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from conftest import login


@pytest.fixture()
def demo(client, db):
    from app.demo_data import DEMO_PASSWORD, demo_accounts, seed_demo

    assert seed_demo(db) is True
    assert seed_demo(db) is False  # idempotent
    return {email.split("@")[0]: login(client, email, DEMO_PASSWORD) for email, _, _ in demo_accounts()}


def test_every_demo_account_signs_in_with_its_role(client, db, demo):
    from app.demo_data import demo_accounts

    for email, name, role in demo_accounts():
        me = client.get("/api/auth/me", headers=demo[email.split("@")[0]]).json()
        assert (me["email"], me["full_name"], me["role"]) == (email, name, role.value)


def test_stats_scopes(client, demo):
    full = client.get("/api/stats/overview", headers=demo["direction"]).json()
    t = full["totals"]
    assert full["scope"] == "all" and set(full["by_institution"]) == {"IIT", "ISB"}
    assert t["preinscriptions"] == 5 and t["enrollments"] == 1 and t["interviews"] == 2 and t["pending"] == 4
    assert [f["label"] for f in full["funnel"]] == ["Conversations", "Orientations", "Pré-inscrits", "Entretiens", "Inscriptions"]
    assert full["agents"]["handoffs"] == 1 and full["agents"]["messages"] == 4 and full["agents"]["sourced_pct"] == 75.0
    assert {p["candidate"] for p in full["pending"]} == {"Fatma Kchaou", "Aziz Trabelsi", "Mariem Kammoun", "Sarra Ayadi"}

    iit = client.get("/api/stats/overview", headers=demo["iit.academique"]).json()
    assert iit["scope"] == "IIT" and "by_institution" not in iit
    assert {p["institution"] for p in iit["programs"]} == {"IIT"} and {p["institution"] for p in iit["pending"]} == {"IIT"}
    assert client.get("/api/stats/overview", headers=demo["iit.academique"], params={"institution": "ISB"}).status_code == 403
    assert client.get("/api/stats/overview", headers=demo["direction"], params={"institution": "ISB"}).json()["scope"] == "ISB"
    assert full["by_institution"]["IIT"]["preinscriptions"] + full["by_institution"]["ISB"]["preinscriptions"] == t["preinscriptions"]


def test_interview_files(client, demo):
    items = client.get("/api/interviews/candidates", headers=demo["entretien"]).json()
    names = [i["name"] for i in items]
    assert names[0] == "Fatma Kchaou"  # the one with an appointment comes first
    assert set(names) == {"Fatma Kchaou", "Aziz Trabelsi"}  # ready = QCM done or appointment booked
    fatma = items[0]
    assert fatma["reference"].startswith("SC-") and fatma["appointment"]["status"] == "confirmed" and fatma["qcm"]["total"] == 12

    d = client.get(f"/api/interviews/candidates/{fatma['id']}", headers=demo["entretien"]).json()
    assert d["recommendation"]["chosen"] == "Licence en informatique" and d["recommendation"]["validated_by_human"] is False
    assert d["qcm_result"]["total"] == 12 and len(d["qcm_result"]["by_section"]) == 3
    assert d["points"] and "relevé de notes" in " ".join(d["points"]) and d["disclaimer"] and "Informatique" in d["summary"]

    # academic heads only see their own institution
    assert {i["institution"] for i in client.get("/api/interviews/candidates", headers=demo["iit.academique"]).json()} == {"IIT"}
    assert client.get("/api/interviews/candidates", headers=demo["isb.academique"]).json() == []
    assert client.get(f"/api/interviews/candidates/{fatma['id']}", headers=demo["isb.academique"]).status_code == 404
    assert client.get("/api/interviews/candidates/9999", headers=demo["entretien"]).status_code == 404


def test_demo_catalogue_is_visible_publicly(client, demo):
    lic = next(p for p in client.get("/api/programs").json() if p["name"] == "Licence en informatique")
    info = client.get(f"/api/programs/{lic['id']}/official-info").json()
    assert info["complete"] == {"fees": True, "payment_terms": True, "admission_conditions": True}
    assert [f["label"] for f in info["fees"]] == ["Frais de scolarité"]  # the draft fee stays hidden
    assert {s["name"] for s in client.get("/api/specialties", params={"program_id": lic["id"]}).json()} == {"Génie logiciel", "Science des données"}
    assert len(client.get("/api/subjects", params={"program_id": lic["id"], "limit": 200}).json()) == 5
    # candidate journey works with the demo candidate
    assert client.get("/api/qcm/current", headers=demo["fatma.kchaou"]).json()["finished"] is True
    assert client.get("/api/appointments/me", headers=demo["fatma.kchaou"]).json()[0]["status"] == "confirmed"


def test_outdated_schema_is_detected():
    from app.db.session import create_tables, schema_problems

    eng = create_engine("sqlite://", poolclass=StaticPool)
    with eng.begin() as c:  # a users table from an older version (no is_active column)
        c.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR, full_name VARCHAR, hashed_password VARCHAR, role VARCHAR, created_at DATETIME)"))
    assert any(p.startswith("users: is_active") for p in schema_problems(eng))
    fresh = create_engine("sqlite://", poolclass=StaticPool)
    create_tables(fresh)
    assert schema_problems(fresh) == []
