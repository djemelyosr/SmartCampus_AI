"""Account state managed by the administrator: active / inactive (reactivable) / blocked (with a reason)."""

from app.core.security import hash_password
from app.db.session import get_db
from app.main import app as api
from app.models.models import Role, User

PWD = "a-long-test-password"


def make_user(email: str, role: Role = Role.interviewer) -> None:
    db = next(api.dependency_overrides[get_db]())
    db.add(User(email=email, full_name=email.split("@")[0], role=role, hashed_password=hash_password(PWD)))
    db.commit()


def login(client, email: str):
    return client.post("/api/auth/login", data={"username": email, "password": PWD})


def bearer(client, email: str) -> dict:
    return {"Authorization": f"Bearer {login(client, email).json()['access_token']}"}


def uid(client, admin: dict, email: str) -> int:
    return next(u["id"] for u in client.get("/api/admin/users", headers=admin).json() if u["email"] == email)


def set_status(client, admin, user_id, status, reason=None):
    return client.put(f"/api/admin/users/{user_id}/status", headers=admin, json={"status": status, "reason": reason})


def test_inactive_then_active_again(client):
    make_user("admin.s@example.com", Role.admin)
    make_user("iv@example.com")
    admin = bearer(client, "admin.s@example.com")
    token = bearer(client, "iv@example.com")  # a session opened before the change
    i = uid(client, admin, "iv@example.com")
    assert client.get("/api/auth/me", headers=token).status_code == 200

    off = set_status(client, admin, i, "inactive").json()
    assert off["is_active"] is False and off["is_blocked"] is False
    denied = login(client, "iv@example.com")
    assert denied.status_code == 403 and "disabled" in denied.json()["detail"].lower()
    assert client.get("/api/auth/me", headers=token).status_code == 403  # the open session is cut at once

    on = set_status(client, admin, i, "active").json()
    assert on["is_active"] is True and login(client, "iv@example.com").status_code == 200


def test_blocked_keeps_the_reason_and_who_did_it(client):
    make_user("admin.s@example.com", Role.admin)
    make_user("iv@example.com")
    admin = bearer(client, "admin.s@example.com")
    token = bearer(client, "iv@example.com")
    i = uid(client, admin, "iv@example.com")

    blocked = set_status(client, admin, i, "blocked", "Partage de mot de passe").json()
    assert blocked["is_blocked"] is True and blocked["is_active"] is False
    assert blocked["blocked_reason"] == "Partage de mot de passe" and blocked["blocked_at"]
    denied = login(client, "iv@example.com")
    assert denied.status_code == 403 and "blocked" in denied.json()["detail"].lower()  # not the same message as an inactive account
    assert client.get("/api/auth/me", headers=token).status_code == 403
    assert next(u for u in client.get("/api/admin/users", headers=admin).json() if u["id"] == i)["blocked_reason"] == "Partage de mot de passe"

    free = set_status(client, admin, i, "active").json()  # lifting the block clears the record
    assert free["is_blocked"] is False and free["blocked_reason"] is None and free["blocked_at"] is None
    assert login(client, "iv@example.com").status_code == 200


def test_a_block_can_be_downgraded_to_inactive(client):
    make_user("admin.s@example.com", Role.admin)
    make_user("iv@example.com")
    admin = bearer(client, "admin.s@example.com")
    i = uid(client, admin, "iv@example.com")
    set_status(client, admin, i, "blocked", "x")
    r = set_status(client, admin, i, "inactive").json()
    assert r["is_blocked"] is False and r["is_active"] is False and r["blocked_reason"] is None
    assert "disabled" in login(client, "iv@example.com").json()["detail"].lower()


def test_patch_reactivation_also_lifts_a_block(client):
    make_user("admin.s@example.com", Role.admin)
    make_user("iv@example.com")
    admin = bearer(client, "admin.s@example.com")
    i = uid(client, admin, "iv@example.com")
    set_status(client, admin, i, "blocked", "x")
    r = client.patch(f"/api/admin/users/{i}", headers=admin, json={"is_active": True}).json()
    assert r["is_active"] is True and r["is_blocked"] is False  # never 'active' and 'blocked' at the same time
    assert login(client, "iv@example.com").status_code == 200


def test_guards(client, auth):
    make_user("admin.s@example.com", Role.admin)
    admin = bearer(client, "admin.s@example.com")
    me = uid(client, admin, "admin.s@example.com")
    for st in ("inactive", "blocked"):
        r = set_status(client, admin, me, st)
        assert r.status_code == 409 and "own status" in r.json()["detail"]  # an administrator cannot lock themselves out
    assert set_status(client, admin, me, "active").status_code == 200

    assert client.put(f"/api/admin/users/{me}/status", headers=admin, json={"status": "suspended"}).status_code == 422
    assert set_status(client, admin, 9999, "blocked").status_code == 404
    assert client.put(f"/api/admin/users/{me}/status", json={"status": "blocked"}).status_code == 401
    assert client.put(f"/api/admin/users/{me}/status", headers=auth, json={"status": "blocked"}).status_code == 403  # a candidate

    pending = client.post("/api/auth/register", json={"email": "p@example.com", "password": PWD, "role": "iit_head"}).json()["id"]
    r = set_status(client, admin, pending, "blocked")
    assert r.status_code == 409 and "not approved" in r.json()["detail"]  # requests are handled with approve / reject
