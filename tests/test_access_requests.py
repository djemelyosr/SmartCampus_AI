"""Sign-up with a role + administrator approval: a team role is only granted once an administrator accepts it."""

from app.core.security import hash_password
from app.db.session import get_db
from app.main import app as api
from app.models.models import Role, User

PWD = "a-long-test-password"


def make_admin(client, email="admin.approval@example.com") -> dict:
    db = next(api.dependency_overrides[get_db]())
    db.add(User(email=email, full_name="Admin", role=Role.admin, hashed_password=hash_password(PWD)))
    db.commit()
    return bearer(client, email)


def bearer(client, email: str) -> dict:
    return {"Authorization": f"Bearer {client.post('/api/auth/login', data={'username': email, 'password': PWD}).json()['access_token']}"}


def sign_up(client, email: str, role: str):
    return client.post("/api/auth/register", json={"email": email, "password": PWD, "full_name": email.split("@")[0], "role": role})


def login(client, email: str):
    return client.post("/api/auth/login", data={"username": email, "password": PWD})


def test_roles_offered_at_sign_up(client):
    roles = {r["role"]: r["needs_approval"] for r in client.get("/api/auth/register/roles").json()}
    assert roles == {"candidate": False, "iit_head": True, "isb_head": True, "interviewer": True, "direction": True}  # never admin


def test_candidate_is_approved_at_once(client):
    r = sign_up(client, "cand@example.com", "candidate")
    assert r.status_code == 201 and r.json()["approval_status"] == "approved" and r.json()["role"] == "candidate"
    assert login(client, "cand@example.com").status_code == 200


def test_team_role_waits_for_an_administrator(client):
    r = sign_up(client, "head@example.com", "iit_head")
    assert r.status_code == 201
    u = r.json()
    assert u["approval_status"] == "pending" and u["requested_role"] == "iit_head"
    assert u["role"] == "candidate"  # no privilege before the decision
    wrong = client.post("/api/auth/login", data={"username": "head@example.com", "password": "not-the-password"})
    assert wrong.status_code == 401  # the pending state is only revealed to the owner of the password
    denied = login(client, "head@example.com")
    assert denied.status_code == 403 and "pending" in denied.json()["detail"].lower()


def test_administrator_approves_and_the_role_is_granted(client):
    admin = make_admin(client)
    uid = sign_up(client, "head@example.com", "iit_head").json()["id"]
    pending = client.get("/api/admin/users?approval=pending", headers=admin).json()
    assert [p["id"] for p in pending] == [uid] and pending[0]["requested_role"] == "iit_head"

    ok = client.post(f"/api/admin/users/{uid}/approve", headers=admin, json={"note": "Confirmé par la direction"})
    assert ok.status_code == 200
    body = ok.json()
    assert body["approval_status"] == "approved" and body["role"] == "iit_head" and body["review_note"] == "Confirmé par la direction" and body["reviewed_at"]
    tok = login(client, "head@example.com")
    assert tok.status_code == 200
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok.json()['access_token']}"}).json()
    assert me["role"] == "iit_head"
    assert client.get("/api/admin/users?approval=pending", headers=admin).json() == []
    assert client.post(f"/api/admin/users/{uid}/approve", headers=admin).status_code == 409  # already decided


def test_administrator_can_grant_another_role_than_requested(client):
    admin = make_admin(client)
    uid = sign_up(client, "dir@example.com", "direction").json()["id"]
    assert client.post(f"/api/admin/users/{uid}/approve", headers=admin, json={"role": "interviewer"}).json()["role"] == "interviewer"


def test_rejected_request_cannot_sign_in_and_can_be_reconsidered(client):
    admin = make_admin(client)
    uid = sign_up(client, "head@example.com", "isb_head").json()["id"]
    rej = client.post(f"/api/admin/users/{uid}/reject", headers=admin, json={"note": "Adresse non reconnue"}).json()
    assert rej["approval_status"] == "rejected" and rej["role"] == "candidate" and rej["review_note"] == "Adresse non reconnue"
    denied = login(client, "head@example.com")
    assert denied.status_code == 403 and "rejected" in denied.json()["detail"].lower()
    assert client.post(f"/api/admin/users/{uid}/reject", headers=admin).status_code == 409  # only pending requests can be rejected
    assert client.post(f"/api/admin/users/{uid}/approve", headers=admin).json()["role"] == "isb_head"  # reconsidered
    assert login(client, "head@example.com").status_code == 200


def test_only_administrators_decide(client, auth):
    uid = sign_up(client, "head@example.com", "iit_head").json()["id"]
    assert client.post(f"/api/admin/users/{uid}/approve").status_code == 401
    assert client.post(f"/api/admin/users/{uid}/approve", headers=auth).status_code == 403  # a candidate
    assert client.post(f"/api/admin/users/{uid}/reject", headers=auth).status_code == 403
    assert login(client, "head@example.com").status_code == 403  # still pending
    assert client.post("/api/admin/users/9999/approve", headers=make_admin(client)).status_code == 404


def test_sign_up_validation(client):
    assert sign_up(client, "x@example.com", "admin").status_code == 422
    assert sign_up(client, "x@example.com", "superuser").status_code == 422
    assert client.post("/api/auth/register", json={"email": "x@example.com", "password": "short"}).status_code == 422
    assert sign_up(client, "dup@example.com", "interviewer").status_code == 201
    assert sign_up(client, "dup@example.com", "candidate").status_code == 409


def test_a_pending_account_token_is_useless(client):
    """Belt and braces: even a valid token of an account that is not approved is refused."""
    from app.core.security import create_access_token

    uid = sign_up(client, "head@example.com", "iit_head").json()["id"]
    token = create_access_token(str(uid), "iit_head")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 403
