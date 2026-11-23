"""Catalogue management, institution scope and the publication workflow of official information."""

from datetime import date, timedelta

import pytest

from conftest import make_user

TODAY = date.today()


@pytest.fixture()
def team(client, db):
    return {
        "iit": make_user(db, client, "iit_head", "iit@example.com"),
        "isb": make_user(db, client, "isb_head", "isb@example.com"),
        "admin": make_user(db, client, "admin", "admin@example.com"),
        "cand": make_user(db, client, "candidate", "cand@example.com"),
    }


def _prog(client, h, inst="IIT", name="Licence test", **kw):
    r = client.post("/api/programs", headers=h, json={"institution": inst, "level": "licence", "name": name, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def test_institution_scope(client, team):
    iit = _prog(client, team["iit"])
    assert client.post("/api/programs", headers=team["iit"], json={"institution": "ISB", "level": "licence", "name": "x"}).status_code == 403
    isb = _prog(client, team["admin"], "ISB", "Gestion test")  # the administrator manages every institution
    # an IIT head cannot touch ISB content, nor move IIT content to ISB
    assert client.patch(f"/api/programs/{isb['id']}", headers=team["iit"], json={"name": "hack"}).status_code == 403
    assert client.patch(f"/api/programs/{iit['id']}", headers=team["iit"], json={"institution": "ISB"}).status_code == 403
    assert client.post("/api/specialties", headers=team["iit"], json={"program_id": isb["id"], "name": "S"}).status_code == 403
    assert client.post("/api/specialties", headers=team["isb"], json={"program_id": isb["id"], "name": "S"}).status_code == 201
    # other roles are read-only
    assert client.post("/api/programs", headers=team["cand"], json={"institution": "IIT", "level": "licence", "name": "x"}).status_code == 403
    assert client.post("/api/programs", json={"institution": "IIT", "level": "licence", "name": "x"}).status_code == 401
    # everybody reads everything (all institutions) — the UI shows other institutions read-only
    assert {p["id"] for p in client.get("/api/programs", headers=team["iit"], params={"include_inactive": "true"}).json()} >= {iit["id"], isb["id"]}


def test_visibility_of_inactive_items(client, team):
    p = _prog(client, team["iit"])
    off = _prog(client, team["iit"], name="Ancienne formation")
    client.patch(f"/api/programs/{off['id']}", headers=team["iit"], json={"active": False})
    s = client.post("/api/specialties", headers=team["iit"], json={"program_id": p["id"], "name": "Cachée"}).json()
    client.patch(f"/api/specialties/{s['id']}", headers=team["iit"], json={"active": False})

    public = {x["id"] for x in client.get("/api/programs").json()}
    assert p["id"] in public and off["id"] not in public
    # visitors cannot see inactive content even when they ask for it
    assert off["id"] not in {x["id"] for x in client.get("/api/programs", params={"include_inactive": "true"}).json()}
    assert client.get(f"/api/programs/{off['id']}").status_code == 404
    assert client.get("/api/specialties", params={"program_id": p["id"]}).json() == []
    assert len(client.get("/api/specialties", headers=team["iit"], params={"program_id": p["id"], "include_inactive": "true"}).json()) == 1


def test_validation_rules(client, team):
    h = team["iit"]
    p = _prog(client, h)
    other = _prog(client, h, name="Autre")
    s = client.post("/api/specialties", headers=h, json={"program_id": p["id"], "name": "Génie logiciel"}).json()
    dup = client.post("/api/specialties", headers=h, json={"program_id": p["id"], "name": "génie LOGICIEL"})
    assert dup.status_code == 409 and "specialty with that name" in dup.json()["detail"]
    assert client.post("/api/curricula", headers=h, json={"program_id": p["id"], "name": "C", "academic_year": "2026-2028"}).status_code == 422
    wrong = client.post("/api/curricula", headers=h, json={"program_id": other["id"], "specialty_id": s["id"], "name": "C"})
    assert wrong.status_code == 422 and "does not belong" in wrong.json()["detail"]
    c = client.post("/api/curricula", headers=h, json={"program_id": p["id"], "specialty_id": s["id"], "name": "C", "academic_year": "2026-2027"}).json()
    assert client.post("/api/subjects", headers=h, json={"curriculum_id": c["id"], "name": "M", "semester": 13}).status_code == 422
    client.post("/api/subjects", headers=h, json={"curriculum_id": c["id"], "name": "M", "code": "INF101", "semester": 1})
    sub = client.post("/api/subjects", headers=h, json={"curriculum_id": c["id"], "name": "M2", "code": "inf101"})
    assert sub.status_code == 409 and "subject with that code" in sub.json()["detail"]
    # required fields cannot be cleared on update
    nul = client.patch(f"/api/specialties/{s['id']}", headers=h, json={"name": None})
    assert nul.status_code == 422 and "cannot be null" in nul.json()["detail"]
    fee = client.post("/api/fees", headers=h, json={"program_id": p["id"], "label": "F", "amount": 10, "currency": "TND", "period": "annual"}).json()
    bad_fee = client.post("/api/payment-terms", headers=h, json={"program_id": other["id"], "fee_id": fee["id"], "method": "cash", "title": "T", "installments": 1})
    assert bad_fee.status_code == 422 and "fee does not belong" in bad_fee.json()["detail"]
    assert client.post("/api/fees", headers=h, json={"program_id": p["id"], "label": "F", "amount": 10, "currency": "dinar", "period": "annual"}).status_code == 422
    period = client.post("/api/fees", headers=h, json={"program_id": p["id"], "label": "F", "amount": 1, "currency": "TND", "period": "annual",
                                                       "valid_from": str(TODAY), "valid_until": str(TODAY - timedelta(days=1))})
    assert period.status_code == 422 and "valid_until must not be before" in period.text


def test_publication_workflow_and_official_info(client, team):
    h = team["iit"]
    p = _prog(client, h)
    fee = client.post("/api/fees", headers=h, json={"program_id": p["id"], "label": "Frais", "amount": 6500, "currency": "TND", "period": "annual"}).json()
    assert fee["status"] == "draft" and fee["official"] is False
    info = client.get(f"/api/programs/{p['id']}/official-info").json()
    assert info["fees"] == [] and info["complete"]["fees"] is False and info["as_of"]
    # drafts are invisible to visitors and candidates, even in lists
    assert client.get("/api/fees", params={"program_id": p["id"], "include_inactive": "true"}).json() == []
    assert client.get("/api/fees", headers=team["cand"], params={"include_inactive": "true"}).json() == []

    pub = client.post(f"/api/fees/{fee['id']}/publish", headers=h).json()
    assert pub["status"] == "published" and pub["official"] is True and pub["published_at"]
    info = client.get(f"/api/programs/{p['id']}/official-info").json()
    assert [f["id"] for f in info["fees"]] == [fee["id"]] and info["complete"]["fees"] is True
    assert client.post(f"/api/fees/{fee['id']}/publish", headers=team["isb"]).status_code == 403

    # changing the content of a published item sends it back to draft; toggling `active` does not
    assert client.patch(f"/api/fees/{fee['id']}", headers=h, json={"active": True}).json()["status"] == "published"
    assert client.patch(f"/api/fees/{fee['id']}", headers=h, json={"amount": 7000}).json()["status"] == "draft"
    client.post(f"/api/fees/{fee['id']}/publish", headers=h)

    # a second published fee with the same label must not cover the same period
    twin = client.post("/api/fees", headers=h, json={"program_id": p["id"], "label": "frais", "amount": 1, "currency": "TND", "period": "annual"}).json()
    clash = client.post(f"/api/fees/{twin['id']}/publish", headers=h)
    assert clash.status_code == 409 and "already covers this period" in clash.json()["detail"]
    # …but it can follow it: the current one ends, the new one starts the next day
    client.patch(f"/api/fees/{fee['id']}", headers=h, json={"valid_until": str(TODAY + timedelta(days=10))})
    client.post(f"/api/fees/{fee['id']}/publish", headers=h)
    client.patch(f"/api/fees/{twin['id']}", headers=h, json={"valid_from": str(TODAY + timedelta(days=11))})
    assert client.post(f"/api/fees/{twin['id']}/publish", headers=h).status_code == 200
    # the upcoming one is published but not "official" yet
    assert [f["id"] for f in client.get(f"/api/programs/{p['id']}/official-info").json()["fees"]] == [fee["id"]]
    upcoming = client.get("/api/fees", headers=h, params={"include_inactive": "true", "validity": "upcoming"}).json()
    assert [f["id"] for f in upcoming] == [twin["id"]] and upcoming[0]["official"] is False

    # expired periods cannot be published; archive hides it
    old = client.post("/api/admission-conditions", headers=h, json={"program_id": p["id"], "kind": "diploma", "title": "Bac",
                                                                     "valid_from": str(TODAY - timedelta(days=30)), "valid_until": str(TODAY - timedelta(days=1))}).json()
    over = client.post(f"/api/admission-conditions/{old['id']}/publish", headers=h)
    assert over.status_code == 409 and "already over" in over.json()["detail"]
    assert client.post(f"/api/fees/{fee['id']}/archive", headers=h).json()["status"] == "archived"
    assert client.get(f"/api/programs/{p['id']}/official-info").json()["fees"] == []
    assert client.post(f"/api/fees/{fee['id']}/unknown", headers=h).status_code == 404
    # filters
    assert [f["id"] for f in client.get("/api/fees", headers=h, params={"include_inactive": "true", "status": "archived"}).json()] == [fee["id"]]


def test_search_filters_and_delete(client, team, db):
    h = team["iit"]
    p = _prog(client, h, name="Licence informatique")
    _prog(client, team["isb"], "ISB", "Licence gestion")
    assert [x["name"] for x in client.get("/api/programs", params={"q": "inform"}).json()] == ["Licence informatique"]
    assert [x["name"] for x in client.get("/api/programs", params={"institution": "ISB"}).json()] == ["Licence gestion"]
    assert client.get("/api/programs", params={"level": "nope"}).status_code == 422

    s = client.post("/api/specialties", headers=h, json={"program_id": p["id"], "name": "S"}).json()
    c = client.post("/api/curricula", headers=h, json={"program_id": p["id"], "specialty_id": s["id"], "name": "C"}).json()
    client.post("/api/subjects", headers=h, json={"curriculum_id": c["id"], "name": "M", "semester": 2})
    assert len(client.get("/api/subjects", params={"program_id": p["id"], "semester": 2}).json()) == 1
    assert client.get("/api/subjects", params={"semester": 3}).json() == []

    # a formation with pre-registrations cannot be deleted (deactivate it instead)
    from app.models.models import PreRegistration, User

    cand_id = db.query(User).filter(User.email == "cand@example.com").one().id
    db.add(PreRegistration(user_id=cand_id, program_id=p["id"]))
    db.commit()
    blocked = client.delete(f"/api/programs/{p['id']}", headers=h)
    assert blocked.status_code == 409 and "pre-registrations" in blocked.json()["detail"]

    # deleting a specialty removes its curricula and subjects
    r = client.delete(f"/api/specialties/{s['id']}", headers=h)
    assert r.status_code == 204 and r.content == b""
    assert client.get(f"/api/curricula/{c['id']}", headers=h).status_code == 404
    assert client.get("/api/subjects", headers=h, params={"include_inactive": "true", "program_id": p["id"]}).json() == []
