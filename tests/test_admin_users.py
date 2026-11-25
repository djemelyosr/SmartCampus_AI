from app.main import app as api
from app.db.session import get_db
from app.core.security import hash_password
from app.models.models import Role, User


def make_admin(client, email="admin.test@example.com", password="a-long-test-password"):
    db = next(api.dependency_overrides[get_db]())
    db.add(User(email=email, full_name="Admin", role=Role.admin, hashed_password=hash_password(password)))
    db.commit()
    tok = client.post("/api/auth/login", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_public_register_never_grants_admin(client):
    body = {"email": "x@example.com", "password": "a-long-test-password", "role": "admin"}
    assert client.post("/api/auth/register", json=body).status_code == 422  # the administrator role is not self-service
    assert client.post("/api/auth/login", data={"username": "x@example.com", "password": "a-long-test-password"}).status_code == 401  # nothing was created
    r = client.post("/api/auth/register", json={k: v for k, v in body.items() if k != "role"})
    assert r.status_code == 201 and r.json()["role"] == "candidate"  # default: an ordinary candidate account


def test_only_admin_can_manage_users(client, auth):
    assert client.get("/api/admin/users", headers=auth).status_code == 403
    assert client.post("/api/admin/users", headers=auth, json={"email": "n@example.com", "password": "a-long-test-password", "role": "admin"}).status_code == 403
    assert client.get("/api/admin/users").status_code == 401


def test_admin_creates_users_with_each_role_and_they_can_log_in(client):
    admin = make_admin(client)
    for role in ("iit_head", "isb_head", "interviewer", "direction", "admin", "candidate"):
        email = f"{role}@example.com"
        r = client.post("/api/admin/users", headers=admin, json={"email": email, "password": "a-long-test-password", "full_name": role, "role": role})
        assert r.status_code == 201 and r.json()["role"] == role
        login = client.post("/api/auth/login", data={"username": email, "password": "a-long-test-password"})
        assert login.status_code == 200
    assert client.post("/api/admin/users", headers=admin, json={"email": "iit_head@example.com", "password": "a-long-test-password"}).status_code == 409
    roles = {u["role"] for u in client.get("/api/admin/users", headers=admin).json()}
    assert {"iit_head", "isb_head", "interviewer", "direction", "admin", "candidate"} <= roles


def test_admin_changes_role_and_disables_account(client, auth):
    admin = make_admin(client)
    uid = next(u["id"] for u in client.get("/api/admin/users", headers=admin).json() if u["email"] == "test.candidate@example.com")
    assert client.patch(f"/api/admin/users/{uid}", headers=admin, json={"role": "interviewer"}).json()["role"] == "interviewer"
    assert client.get("/api/admin/users?role=interviewer", headers=admin).json()[0]["id"] == uid
    assert client.patch(f"/api/admin/users/{uid}", headers=admin, json={"is_active": False}).json()["is_active"] is False
    # a disabled account can no longer log in nor use an existing token
    assert client.post("/api/auth/login", data={"username": "test.candidate@example.com", "password": "a-long-test-password"}).status_code == 403
    assert client.get("/api/auth/me", headers=auth).status_code == 403
    client.patch(f"/api/admin/users/{uid}", headers=admin, json={"is_active": True})
    assert client.get("/api/auth/me", headers=auth).status_code == 200


def test_cannot_remove_the_last_active_admin(client):
    admin = make_admin(client)
    me = client.get("/api/auth/me", headers=admin).json()
    assert client.patch(f"/api/admin/users/{me['id']}", headers=admin, json={"role": "candidate"}).status_code == 409
    assert client.patch(f"/api/admin/users/{me['id']}", headers=admin, json={"is_active": False}).status_code == 409
