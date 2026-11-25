from conftest import register

from app.core.security import hash_password
from app.db.session import get_db
from app.main import app as api
from app.models.models import Institution, Level, Program, Role, User

PWD = "a-long-team-password"


def _team(client, role: Role, email: str) -> dict:
    db = next(api.dependency_overrides[get_db]())
    db.add(User(email=email, full_name=role.value, role=role, hashed_password=hash_password(PWD)))
    db.commit()
    tok = client.post("/api/auth/login", data={"username": email, "password": PWD}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _prog(inst: Institution, level: Level, name: str) -> int:
    db = next(api.dependency_overrides[get_db]())
    p = Program(institution=inst, level=level, name=name)
    db.add(p)
    db.commit()
    return p.id


def _preinscribe(client, headers, program_id):
    client.put("/api/auth/me/profile", headers=headers, json={"consent_given": True})
    assert client.post("/api/preinscriptions", headers=headers, json={"program_id": program_id}).status_code == 201


def test_qcm_is_targeted_to_institution_and_level(client):
    isb = _prog(Institution.ISB, Level.licence, "Parcours en gestion")
    prepa = _prog(Institution.IIT, Level.prepa, "Cycle préparatoire")
    a = register(client, "isb.cand@example.com")
    _preinscribe(client, a, isb)
    qa = client.get("/api/qcm/current", headers=a).json()
    assert qa["questions"][0]["section"] == "Calcul & raisonnement" and all("correct" not in q for q in qa["questions"])
    b = register(client, "prepa.cand@example.com")
    _preinscribe(client, b, prepa)
    qb = client.get("/api/qcm/current", headers=b).json()
    assert any("limite" in q["text"] for q in qb["questions"])  # harder maths for the prepa track


def test_stats_are_role_scoped(client, auth, program):
    _preinscribe(client, auth, program)
    assert client.get("/api/stats/overview", headers=auth).status_code == 403  # candidates never see stats
    direction = _team(client, Role.direction, "dir@example.com")
    s = client.get("/api/stats/overview", headers=direction).json()
    assert s["totals"]["preinscriptions"] == 1 and set(s["by_institution"]) == {"IIT", "ISB"}
    assert [p["name"] for p in s["programs"]] == ["Licence en informatique"]
    isb_head = _team(client, Role.isb_head, "isb@example.com")
    mine = client.get("/api/stats/overview", params={"institution": "IIT"}, headers=isb_head).json()
    assert mine["scope"] == "ISB" and mine["totals"]["preinscriptions"] == 0  # the query cannot widen a head's scope


def test_interview_brief(client, auth, program):
    _preinscribe(client, auth, program)
    assert client.get("/api/interviews/candidates", headers=auth).status_code == 403
    iv = _team(client, Role.interviewer, "iv@example.com")
    rows = client.get("/api/interviews/candidates", headers=iv).json()
    assert len(rows) == 1 and rows[0]["qcm"] is None
    detail = client.get(f"/api/interviews/candidates/{rows[0]['id']}", headers=iv).json()
    assert detail["recommendation"]["validated_by_human"] is False and detail["points"]
    assert any("QCM" in p for p in detail["points"])  # unfinished QCM is flagged
    isb_head = _team(client, Role.isb_head, "isb2@example.com")
    assert client.get(f"/api/interviews/candidates/{rows[0]['id']}", headers=isb_head).status_code == 404  # other institution
