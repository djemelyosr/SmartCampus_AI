from app.core.security import hash_password
from app.db.session import get_db
from app.main import app as api
from app.models.models import Role, User

PWD = "a-long-test-password"


def staff(client, role: Role, email: str) -> dict:
    db = next(api.dependency_overrides[get_db]())
    db.add(User(email=email, full_name=role.value, role=role, hashed_password=hash_password(PWD)))
    db.commit()
    tok = client.post("/api/auth/login", data={"username": email, "password": PWD}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_demo_catalogue_is_idempotent_and_publicly_readable(client):
    from app.seed import seed_programs
    from app.seed_catalog import seed_catalog

    db = next(api.dependency_overrides[get_db]())
    seed_programs(db)
    first = seed_catalog(db)
    assert all(n > 0 for n in first.values())
    assert seed_catalog(db) == dict.fromkeys(first, 0)  # second run adds nothing

    lic = next(p for p in client.get("/api/programs").json() if p["name"] == "Licence en informatique")
    assert lic["duration_years"] == 3 and not lic["admission_requirements"].startswith("À confirmer")
    assert len(client.get(f"/api/specialties?program_id={lic['id']}").json()) == 3
    assert len(client.get(f"/api/curricula?program_id={lic['id']}").json()) == 4
    subjects = client.get(f"/api/subjects?program_id={lic['id']}&limit=200").json()
    assert len(subjects) == 8 + 6 * 3 and all(s["credits"] and s["hours"] for s in subjects)
    fees = client.get(f"/api/fees?program_id={lic['id']}").json()
    assert {"Frais d'inscription", "Scolarité annuelle"} <= {f["label"] for f in fees}
    assert all(f["currency"] == "TND" for f in fees)
    conditions = client.get(f"/api/admission-conditions?program_id={lic['id']}").json()
    assert any(c["kind"] == "average" and c["threshold"] == 11 for c in conditions)


def test_fee_write_access_and_validation(client, auth):
    from app.seed import seed_programs
    from app.seed_catalog import seed_catalog

    db = next(api.dependency_overrides[get_db]())
    seed_programs(db)
    seed_catalog(db)
    iit = staff(client, Role.iit_head, "iit.fees@example.com")
    isb = staff(client, Role.isb_head, "isb.fees@example.com")
    prog = next(p for p in client.get("/api/programs").json() if p["name"] == "Cycle préparatoire")
    body = {"program_id": prog["id"], "label": "Cantine", "amount": 120.5, "period": "semester"}

    assert client.post("/api/fees", json=body).status_code == 401
    assert client.post("/api/fees", headers=auth, json=body).status_code == 403  # candidate
    assert client.post("/api/fees", headers=isb, json=body).status_code == 403  # other institution
    assert client.post("/api/fees", headers=iit, json={**body, "amount": -1}).status_code == 422
    other_spec = client.get("/api/specialties").json()[0]  # belongs to another formation
    assert client.post("/api/fees", headers=iit, json={**body, "specialty_id": other_spec["id"]}).status_code == 422

    fee = client.post("/api/fees", headers=iit, json=body)
    assert fee.status_code == 201 and fee.json()["currency"] == "TND"
    fid = fee.json()["id"]
    assert client.patch(f"/api/fees/{fid}", headers=iit, json={"amount": 99}).json()["amount"] == 99
    assert client.patch(f"/api/fees/{fid}", headers=iit, json={"active": False}).json()["active"] is False
    assert fid not in [f["id"] for f in client.get(f"/api/fees?program_id={prog['id']}").json()]  # hidden from the public
    assert client.get(f"/api/fees/{fid}").status_code == 404
    assert client.delete(f"/api/fees/{fid}", headers=iit).status_code == 204
