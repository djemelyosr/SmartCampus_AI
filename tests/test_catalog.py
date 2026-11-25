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


def build(client, h):
    """IIT formation + specialty + programme + subject + condition, created by the IIT head."""
    p = client.post("/api/programs", headers=h, json={"institution": "IIT", "level": "ingenierie", "name": "Cycle ingénieur", "duration_years": 3}).json()
    s = client.post("/api/specialties", headers=h, json={"program_id": p["id"], "name": "Génie logiciel"}).json()
    c = client.post("/api/curricula", headers=h, json={"program_id": p["id"], "specialty_id": s["id"], "name": "Programme GL", "academic_year": "2026-2027"}).json()
    m = client.post("/api/subjects", headers=h, json={"curriculum_id": c["id"], "name": "Algorithmique", "code": "ALGO1", "semester": 1, "credits": 5, "coefficient": 2.5, "hours": 42}).json()
    a = client.post("/api/admission-conditions", headers=h, json={"program_id": p["id"], "specialty_id": s["id"], "kind": "average", "title": "Moyenne minimale", "threshold": 12, "status": "published"}).json()
    return p, s, c, m, a


def test_write_access_is_limited_to_academic_heads(client, auth):
    iit = staff(client, Role.iit_head, "iit.test@example.com")
    body = {"institution": "IIT", "level": "licence", "name": "Licence test"}
    assert client.post("/api/programs", json=body).status_code == 401
    assert client.post("/api/programs", headers=auth, json=body).status_code == 403  # candidate
    assert client.post("/api/programs", headers=iit, json=body).status_code == 201
    assert client.post("/api/subjects", headers=auth, json={"curriculum_id": 1, "name": "x"}).status_code == 403


def test_head_only_manages_own_institution_admin_manages_all(client):
    iit = staff(client, Role.iit_head, "iit.test@example.com")
    isb = staff(client, Role.isb_head, "isb.test@example.com")
    admin = staff(client, Role.admin, "admin.test@example.com")
    p, s, c, m, a = build(client, iit)
    assert client.post("/api/programs", headers=iit, json={"institution": "ISB", "level": "licence", "name": "Hors périmètre"}).status_code == 403
    assert client.patch(f"/api/programs/{p['id']}", headers=isb, json={"name": "Piraté"}).status_code == 403
    assert client.post("/api/specialties", headers=isb, json={"program_id": p["id"], "name": "Autre"}).status_code == 403
    assert client.patch(f"/api/subjects/{m['id']}", headers=isb, json={"credits": 1}).status_code == 403
    assert client.delete(f"/api/admission-conditions/{a['id']}", headers=isb).status_code == 403
    assert client.patch(f"/api/programs/{p['id']}", headers=iit, json={"institution": "ISB"}).status_code == 403  # cannot hand it over
    assert client.patch(f"/api/programs/{p['id']}", headers=admin, json={"description": "ok"}).json()["description"] == "ok"


def test_crud_and_cascade(client):
    h = staff(client, Role.iit_head, "iit.test@example.com")
    p, s, c, m, a = build(client, h)
    assert client.get(f"/api/programs/{p['id']}").json()["duration_years"] == 3
    detail = client.get(f"/api/curricula/{c['id']}").json()
    assert [x["code"] for x in detail["subjects"]] == ["ALGO1"] and detail["academic_year"] == "2026-2027"

    upd = client.patch(f"/api/subjects/{m['id']}", headers=h, json={"credits": 6, "hours": None}).json()
    assert upd["credits"] == 6 and upd["hours"] is None and upd["name"] == "Algorithmique"
    assert client.patch(f"/api/subjects/{m['id']}", headers=h, json={"name": None}).status_code == 422
    assert client.patch(f"/api/specialties/{s['id']}", headers=h, json={"name": "GL & DevOps"}).json()["name"] == "GL & DevOps"
    assert client.patch(f"/api/admission-conditions/{a['id']}", headers=h, json={"threshold": 13.5, "required": False}).json()["required"] is False

    assert client.delete(f"/api/subjects/{m['id']}", headers=h).status_code == 204
    assert client.get(f"/api/subjects/{m['id']}").status_code == 404
    m2 = client.post("/api/subjects", headers=h, json={"curriculum_id": c["id"], "name": "Réseaux"}).json()
    assert client.delete(f"/api/programs/{p['id']}", headers=h).status_code == 204  # cascades to everything below
    for url in (f"/api/specialties/{s['id']}", f"/api/curricula/{c['id']}", f"/api/subjects/{m2['id']}", f"/api/admission-conditions/{a['id']}"):
        assert client.get(url).status_code == 404


def test_validation_and_consistency(client):
    h = staff(client, Role.iit_head, "iit.test@example.com")
    p, s, c, m, a = build(client, h)
    p2 = client.post("/api/programs", headers=h, json={"institution": "IIT", "level": "licence", "name": "Licence"}).json()
    assert client.post("/api/specialties", headers=h, json={"program_id": p["id"], "name": "Génie logiciel"}).status_code == 409
    assert client.post("/api/specialties", headers=h, json={"program_id": 999, "name": "x"}).status_code == 404
    assert client.post("/api/specialties", headers=h, json={"program_id": p["id"], "name": ""}).status_code == 422
    assert client.post("/api/subjects", headers=h, json={"curriculum_id": c["id"], "name": "Doublon", "code": "ALGO1"}).status_code == 409
    assert client.post("/api/subjects", headers=h, json={"curriculum_id": c["id"], "name": "Sem", "semester": 13}).status_code == 422
    assert client.post("/api/curricula", headers=h, json={"program_id": p["id"], "name": "Année", "academic_year": "2026"}).status_code == 422
    # a specialty must belong to the formation it is attached to
    assert client.post("/api/curricula", headers=h, json={"program_id": p2["id"], "specialty_id": s["id"], "name": "X"}).status_code == 422
    assert client.post("/api/admission-conditions", headers=h, json={"program_id": p2["id"], "specialty_id": s["id"], "title": "X"}).status_code == 422
    assert client.patch(f"/api/programs/{p['id']}", headers=h, json={"duration_years": 0}).status_code == 422


def test_search_filter_and_pagination(client):
    h = staff(client, Role.iit_head, "iit.test@example.com")
    p, s, c, m, a = build(client, h)
    client.post("/api/subjects", headers=h, json={"curriculum_id": c["id"], "name": "Bases de données", "code": "BD1", "semester": 2, "credits": 3})
    client.post("/api/subjects", headers=h, json={"curriculum_id": c["id"], "name": "Réseaux", "semester": 2, "credits": 4})
    client.post("/api/programs", headers=h, json={"institution": "IIT", "level": "licence", "name": "Licence info", "description": "Développement"})
    client.post("/api/admission-conditions", headers=h, json={"program_id": p["id"], "kind": "diploma", "title": "Baccalauréat", "status": "published"})

    assert [x["name"] for x in client.get("/api/programs?q=licence").json()] == ["Licence info"]
    assert [x["name"] for x in client.get("/api/programs?level=ingenierie&min_duration_years=3").json()] == ["Cycle ingénieur"]
    assert client.get("/api/programs?q=100%25").json() == []  # LIKE wildcards are escaped
    assert {x["name"] for x in client.get("/api/subjects?semester=2").json()} == {"Bases de données", "Réseaux"}
    assert [x["name"] for x in client.get("/api/subjects?q=algo").json()] == ["Algorithmique"]
    assert [x["name"] for x in client.get("/api/subjects?q=BD1").json()] == ["Bases de données"]  # search on the code
    assert {x["name"] for x in client.get(f"/api/subjects?program_id={p['id']}&min_credits=4").json()} == {"Algorithmique", "Réseaux"}
    assert len(client.get(f"/api/subjects?specialty_id={s['id']}&institution=ISB").json()) == 0
    assert [x["name"] for x in client.get("/api/specialties?q=logiciel").json()] == ["Génie logiciel"]
    assert [x["name"] for x in client.get("/api/curricula?academic_year=2026-2027").json()] == ["Programme GL"]
    assert [x["title"] for x in client.get("/api/admission-conditions?kind=average").json()] == ["Moyenne minimale"]
    assert len(client.get(f"/api/admission-conditions?specialty_id={s['id']}").json()) == 1
    assert len(client.get(f"/api/admission-conditions?specialty_id={s['id']}&include_program_wide=true").json()) == 2

    r = client.get("/api/subjects?limit=2&offset=1")
    assert len(r.json()) == 2 and r.headers["X-Total-Count"] == "3"
    assert client.get("/api/subjects?limit=0").status_code == 422


def test_inactive_items_are_hidden_from_the_public(client, auth):
    iit = staff(client, Role.iit_head, "iit.test@example.com")
    isb = staff(client, Role.isb_head, "isb.test@example.com")
    p, s, c, m, a = build(client, iit)
    client.patch(f"/api/subjects/{m['id']}", headers=iit, json={"active": False})
    assert client.get("/api/subjects").json() == [] and client.get(f"/api/subjects/{m['id']}").status_code == 404
    assert client.get(f"/api/curricula/{c['id']}").json()["subjects"] == []
    assert client.get("/api/subjects?include_inactive=true").status_code == 401
    assert client.get("/api/subjects?include_inactive=true", headers=auth).status_code == 403
    assert len(client.get("/api/subjects?include_inactive=true", headers=iit).json()) == 1
    assert client.get("/api/subjects?include_inactive=true", headers=isb).json() == []  # not their institution
    assert len(client.get(f"/api/curricula/{c['id']}", headers=iit).json()["subjects"]) == 1
    # deactivating a formation hides everything under it
    client.patch(f"/api/programs/{p['id']}", headers=iit, json={"active": False})
    assert client.get("/api/programs").json() == [] and client.get(f"/api/programs/{p['id']}").status_code == 404
    assert client.get("/api/specialties").json() == [] and client.get("/api/admission-conditions").json() == []
    assert client.get(f"/api/programs/{p['id']}", headers=iit).status_code == 200


def test_formation_with_preinscriptions_cannot_be_deleted(client, auth, program):
    from app.models.models import PreRegistration

    admin = staff(client, Role.admin, "admin.test@example.com")
    db = next(api.dependency_overrides[get_db]())
    db.add(PreRegistration(user_id=1, program_id=program))
    db.commit()
    assert client.delete(f"/api/programs/{program}", headers=admin).status_code == 409
    assert client.patch(f"/api/programs/{program}", headers=admin, json={"active": False}).json()["active"] is False


def test_search_ignores_case_and_accents(client):
    iit = staff(client, Role.iit_head, "iit.test@example.com")
    p, s, c, m, a = build(client, iit)  # "Cycle ingénieur" / "Génie logiciel" / "Programme GL" / "Algorithmique"
    ids = lambda path, q: [x["id"] for x in client.get(path, params={"q": q}).json()]
    assert ids("/api/programs", "ingenieur") == [p["id"]]  # typed without the accent
    assert ids("/api/programs", "INGÉNIEUR") == [p["id"]]  # uppercase, with the accent
    assert ids("/api/specialties", "genie logiciel") == [s["id"]]
    assert ids("/api/specialties", "génie") == [s["id"]]
    assert ids("/api/subjects", "algo") == [m["id"]]
    assert ids("/api/programs", "licence") == []  # still a real filter
    assert ids("/api/programs", "100%") == []  # LIKE wildcards stay escaped
