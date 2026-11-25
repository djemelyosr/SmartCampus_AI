"""Official information: fees, payment terms and admission conditions with a publication status and a validity period.
Candidates and the AI agent only ever see what is published AND valid today."""

from datetime import timedelta

from app.agents.language import intents_in
from app.core.dates import tn_today
from app.core.security import hash_password
from app.db.session import get_db
from app.main import app as api
from app.models.catalog import Fee
from app.models.models import Role, User

PWD = "a-long-test-password"


def _db():
    return next(api.dependency_overrides[get_db]())


def staff(client, role: Role, email: str) -> dict:
    db = _db()
    db.add(User(email=email, full_name=role.value, role=role, hashed_password=hash_password(PWD)))
    db.commit()
    tok = client.post("/api/auth/login", data={"username": email, "password": PWD}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def day(offset: int) -> str:
    return (tn_today() + timedelta(days=offset)).isoformat()


def new_program(client, h, name="Licence test") -> dict:
    return client.post("/api/programs", headers=h, json={"institution": "IIT", "level": "licence", "name": name}).json()


def new_fee(client, h, program_id, label="Scolarité annuelle", amount=7200, **extra):
    r = client.post("/api/fees", headers=h, json={"program_id": program_id, "label": label, "amount": amount, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def expire(fee_id: int) -> None:
    """Let time pass: the validity period of a published fee ends yesterday."""
    db = _db()
    db.get(Fee, fee_id).valid_until = tn_today() - timedelta(days=1)
    db.commit()


def seed(client):
    from app.seed import seed_programs
    from app.seed_catalog import seed_catalog

    db = _db()
    seed_programs(db)
    seed_catalog(db)
    return next(p for p in client.get("/api/programs").json() if p["name"] == "Licence en informatique")


# --- lifecycle ---------------------------------------------------------------------------------------------------------
def test_fee_lifecycle_draft_publish_edit_archive(client, auth):
    h = staff(client, Role.iit_head, "iit.official@example.com")
    fee = new_fee(client, h, new_program(client, h)["id"])
    fid = fee["id"]
    assert fee["status"] == "draft" and fee["official"] is False  # new items start as drafts

    assert client.get("/api/fees").json() == []  # drafts are invisible to the public...
    assert client.get(f"/api/fees/{fid}").status_code == 404
    assert client.get(f"/api/fees/{fid}", headers=auth).status_code == 404  # ...and to candidates
    assert client.get(f"/api/fees/{fid}", headers=h).status_code == 200  # but the head can work on them
    assert [f["id"] for f in client.get("/api/fees?include_inactive=true", headers=h).json()] == [fid]

    pub = client.post(f"/api/fees/{fid}/publish", headers=h).json()
    assert pub["status"] == "published" and pub["official"] and pub["published_at"]
    assert [f["id"] for f in client.get("/api/fees").json()] == [fid]

    edited = client.patch(f"/api/fees/{fid}", headers=h, json={"amount": 7500}).json()  # content change -> approve again
    assert edited["status"] == "draft" and edited["published_at"] is None and edited["amount"] == 7500
    assert client.get("/api/fees").json() == []

    client.post(f"/api/fees/{fid}/publish", headers=h)
    assert client.patch(f"/api/fees/{fid}", headers=h, json={"active": False}).json()["status"] == "published"  # hiding needs no re-approval
    assert client.get("/api/fees").json() == []
    client.patch(f"/api/fees/{fid}", headers=h, json={"active": True})
    assert client.post(f"/api/fees/{fid}/archive", headers=h).json()["status"] == "archived"
    assert client.get("/api/fees").json() == []
    assert client.post(f"/api/fees/{fid}/draft", headers=h).json()["status"] == "draft"


def test_validity_period_controls_visibility(client):
    h = staff(client, Role.iit_head, "iit.official@example.com")
    isb = staff(client, Role.isb_head, "isb.official@example.com")
    pid = new_program(client, h)["id"]
    current = new_fee(client, h, pid, "Courante", valid_from=day(-10), valid_until=day(10), status="published")
    future = new_fee(client, h, pid, "Future", valid_from=day(5), status="published")
    ended = new_fee(client, h, pid, "Passée", valid_from=day(-400), valid_until=day(30), status="published")
    expire(ended["id"])  # was official, its period is now over

    assert [f["label"] for f in client.get("/api/fees").json()] == ["Courante"]
    assert client.get(f"/api/fees/{future['id']}").status_code == 404 and client.get(f"/api/fees/{ended['id']}").status_code == 404
    assert client.get(f"/api/fees/{current['id']}").json()["official"] is True

    labels = lambda q, hh: sorted(f["label"] for f in client.get(f"/api/fees?include_inactive=true&{q}", headers=hh).json())  # noqa: E731
    assert labels("validity=upcoming", h) == ["Future"] and labels("validity=expired", h) == ["Passée"]
    assert labels("validity=current", h) == ["Courante"] and labels("status=published", h) == ["Courante", "Future", "Passée"]
    assert labels("", isb) == ["Courante"]  # another institution's head only sees what is official


def test_validation_and_overlapping_periods(client):
    h = staff(client, Role.iit_head, "iit.official@example.com")
    pid = new_program(client, h)["id"]
    base = {"program_id": pid, "label": "Scolarité", "amount": 7000}
    post = lambda **kw: client.post("/api/fees", headers=h, json={**base, **kw})  # noqa: E731

    assert post(valid_from=day(5), valid_until=day(1)).status_code == 422  # ends before it starts
    assert post(status="archived").status_code == 422
    assert post(status="published", valid_until=day(-1)).status_code == 422  # already over: nothing to publish
    assert client.get("/api/fees?include_inactive=true", headers=h).json() == []  # the refused publication left nothing behind

    old = post(status="published", valid_from=day(-30), valid_until=day(30))
    assert old.status_code == 201
    assert post(status="published", amount=7500, valid_from=day(10)).status_code == 409  # same days, same tariff
    assert post(status="published", label="Autre frais", valid_from=day(10)).status_code == 201  # other label: no conflict
    assert post(status="published", amount=7500, valid_from=day(31)).status_code == 201  # takes over the day after

    draft = post(valid_from=day(0), valid_until=day(20)).json()
    assert client.post(f"/api/fees/{draft['id']}/publish", headers=h).status_code == 409
    client.post(f"/api/fees/{old.json()['id']}/archive", headers=h)  # withdrawing the old one frees the period
    assert client.post(f"/api/fees/{draft['id']}/publish", headers=h).status_code == 200
    assert client.patch(f"/api/fees/{draft['id']}", headers=h, json={"valid_from": day(9), "valid_until": day(1)}).status_code == 422


def test_status_changes_are_limited_to_the_institution_head(client, auth):
    iit = staff(client, Role.iit_head, "iit.official@example.com")
    isb = staff(client, Role.isb_head, "isb.official@example.com")
    admin = staff(client, Role.admin, "admin.official@example.com")
    fid = new_fee(client, iit, new_program(client, iit)["id"])["id"]
    url = f"/api/fees/{fid}/publish"
    assert client.post(url).status_code == 401
    assert client.post(url, headers=auth).status_code == 403  # candidate
    assert client.post(url, headers=isb).status_code == 403  # other institution
    assert client.get(f"/api/fees/{fid}", headers=isb).status_code == 404  # not even visible to them
    assert client.get("/api/fees?include_inactive=true").status_code == 401
    assert client.get("/api/fees?include_inactive=true", headers=auth).status_code == 403
    assert client.post(url, headers=admin).json()["status"] == "published"


# --- payment terms ---------------------------------------------------------------------------------------------------------
def test_payment_terms(client, auth):
    h = staff(client, Role.iit_head, "iit.official@example.com")
    pid, other = new_program(client, h)["id"], new_program(client, h, "Autre licence")["id"]
    fee = new_fee(client, h, pid, status="published")
    body = {"program_id": pid, "title": "Virement en 3 tranches", "method": "bank_transfer", "installments": 3, "down_payment_percent": 40, "fee_id": fee["id"]}

    assert client.post("/api/payment-terms", headers=h, json={**body, "fee_id": new_fee(client, h, other)["id"]}).status_code == 422  # fee of another formation
    assert client.post("/api/payment-terms", headers=h, json={**body, "installments": 0}).status_code == 422
    assert client.post("/api/payment-terms", headers=h, json={**body, "down_payment_percent": 120}).status_code == 422
    assert client.post("/api/payment-terms", headers=auth, json=body).status_code == 403

    term = client.post("/api/payment-terms", headers=h, json=body).json()
    tid = term["id"]
    assert term["status"] == "draft" and client.get("/api/payment-terms").json() == []
    assert client.post(f"/api/payment-terms/{tid}/publish", headers=h).json()["official"] is True
    assert [t["id"] for t in client.get(f"/api/payment-terms?program_id={pid}&method=bank_transfer&fee_id={fee['id']}").json()] == [tid]
    assert client.get("/api/payment-terms?method=cash").json() == []

    patched = client.patch(f"/api/payment-terms/{tid}", headers=h, json={"due_date": day(20), "down_payment_percent": None}).json()
    assert patched["status"] == "draft" and patched["due_date"] == day(20) and patched["down_payment_percent"] is None
    assert client.delete(f"/api/programs/{pid}", headers=h).status_code == 204  # removed with the formation
    assert client.get(f"/api/payment-terms/{tid}", headers=h).status_code == 404


# --- what candidates and the agent consult ---------------------------------------------------------------------------------
def test_official_info_endpoint_only_returns_official_items(client, auth):
    lic = seed(client)
    h = staff(client, Role.iit_head, "iit.official@example.com")
    new_fee(client, h, lic["id"], "Frais brouillon", 99999)  # draft
    gone = new_fee(client, h, lic["id"], "Ancien tarif", 11111, status="published")
    expire(gone["id"])

    info = client.get(f"/api/programs/{lic['id']}/official-info", headers=auth).json()
    assert info["as_of"] == tn_today().isoformat() and info["complete"] == {"fees": True, "payment_terms": True, "admission_conditions": True}
    labels = {f["label"] for f in info["fees"]}
    assert {"Scolarité annuelle", "Frais d'inscription"} <= labels and not ({"Frais brouillon", "Ancien tarif"} & labels)
    assert all(x["official"] for x in info["fees"] + info["payment_terms"] + info["admission_conditions"])

    specialties = {s["name"]: s["id"] for s in client.get(f"/api/specialties?program_id={lic['id']}").json()}
    narrow = client.get(f"/api/programs/{lic['id']}/official-info?specialty_id={specialties['Data et intelligence artificielle']}").json()
    narrow_labels = {f["label"] for f in narrow["fees"]}
    assert "Laboratoire et licences logicielles" in narrow_labels and "Matériel de laboratoire réseau" not in narrow_labels and "Scolarité annuelle" in narrow_labels
    other = new_program(client, h, "Autre")  # specialty of another formation
    assert client.get(f"/api/programs/{other['id']}/official-info?specialty_id={specialties['Réseaux et systèmes']}").status_code == 422

    assert client.get(f"/api/programs/{other['id']}/official-info").json()["complete"] == {"fees": False, "payment_terms": False, "admission_conditions": False}
    client.patch(f"/api/programs/{other['id']}", headers=h, json={"active": False})
    assert client.get(f"/api/programs/{other['id']}/official-info").status_code == 404


# --- the AI agent only reads official information ----------------------------------------------------------------------------
def chat(client, auth, text, cid=None):
    cid = cid or client.post("/api/conversations", headers=auth).json()["id"]
    r = client.post(f"/api/conversations/{cid}/messages", json={"content": text}, headers=auth)
    assert r.status_code == 200, r.text
    return cid, r.json()


def test_agent_quotes_only_official_fees_and_payment_terms(client, auth):
    lic = seed(client)
    h = staff(client, Role.iit_head, "iit.official@example.com")
    new_fee(client, h, lic["id"], "Frais secret brouillon", 99999)
    gone = new_fee(client, h, lic["id"], "Ancien tarif", 11111, status="published")
    expire(gone["id"])

    cid, m = chat(client, auth, "Quels sont les frais de scolarité de la licence en informatique ?")
    text = m["content"]
    assert m["meta"]["action"] == "rag_frais" and m["meta"]["official"]["found"] and m["meta"]["official"]["as_of"] == tn_today().isoformat()
    assert "7 200" in text and "350" in text
    assert not any(x in text for x in ("99999", "99 999", "11111", "11 111", "secret", "Ancien"))

    _, m = chat(client, auth, "et les modalités de paiement ?", cid)  # the formation comes from the session memory
    assert m["meta"]["action"] == "rag_paiement" and "3 versements" in m["content"] and "40 %" in m["content"]

    _, m = chat(client, auth, "Quelles sont les conditions d’accès, la scolarité et le paiement ?", cid)
    assert m["meta"]["action"] == "rag_conditions_frais_paiement" and "11" in m["content"]  # seuil de la moyenne
    _, m = chat(client, auth, "Quelles sont les conditions d’accès, la scolarité et le paiement ?")  # no formation known yet
    assert m["meta"]["action"] == "no_source_handoff"  # it does not guess which formation is meant


def test_agent_never_invents_what_is_not_official(client, auth, program):
    h = staff(client, Role.iit_head, "iit.official@example.com")
    ask = lambda: chat(client, auth, "Quels sont les frais de la licence en informatique ?")[1]  # noqa: E731
    m = ask()
    assert m["meta"]["action"] == "no_source_handoff" and m["meta"]["handoff"] is True  # nothing published yet

    fee = new_fee(client, h, program, "Scolarité annuelle", 6400)
    assert ask()["meta"]["action"] == "no_source_handoff"  # a draft is not official

    client.post(f"/api/fees/{fee['id']}/publish", headers=h)
    m = ask()
    assert m["meta"]["action"] == "rag_frais" and "6 400" in m["content"]

    expire(fee["id"])
    assert ask()["meta"]["action"] == "no_source_handoff"  # validity period over
    client.patch(f"/api/fees/{fee['id']}", headers=h, json={"valid_until": None})
    client.post(f"/api/fees/{fee['id']}/publish", headers=h)
    assert ask()["meta"]["action"] == "rag_frais"
    client.post(f"/api/fees/{fee['id']}/archive", headers=h)
    assert ask()["meta"]["action"] == "no_source_handoff"  # withdrawn


def test_agent_understands_money_questions_in_every_language(client, auth):
    seed(client)
    assert not client.get("/api/preinscriptions", headers=auth).json()
    _, m = chat(client, auth, "Combien coûtent les frais d’inscription à la licence en informatique ?")
    assert m["meta"]["action"] == "rag_frais" and not client.get("/api/preinscriptions", headers=auth).json()  # not a registration

    _, m = chat(client, auth, "9addech el ma3alim mta3 licence informatique")
    assert m["meta"]["language"] == "arabizi" and m["meta"]["action"] == "rag_frais" and m["content"].startswith("Ma3alim el dirassa")
    _, m = chat(client, auth, "شنوة معاليم ليسانس إعلامية؟")
    assert m["meta"]["language"] == "tn" and m["meta"]["action"] == "rag_frais" and "معاليم الدراسة" in m["content"]


def test_intents_for_money_questions():
    assert intents_in("Quels sont les frais d’inscription ?") == ["frais"]
    assert "preinscription" in intents_in("Je veux m’inscrire, combien ça coûte ?")
    assert intents_in("Quelles sont les conditions de paiement ?") == ["paiement"]
    assert set(intents_in("conditions d’admission et modalités de paiement")) == {"conditions", "paiement"}
