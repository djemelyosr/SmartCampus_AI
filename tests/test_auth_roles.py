"""Authentication, roles and API protection."""

from conftest import PW, login, make_user, register


def test_register_rules(client):
    short = client.post("/api/auth/register", json={"email": "a@example.com", "password": "short-pw", "full_name": "A"})
    assert short.status_code == 422  # same 12-character rule as the frontend
    r = client.post("/api/auth/register", json={"email": "New.User@Example.com", "password": PW, "full_name": " New "})
    assert r.status_code == 201 and r.json()["role"] == "candidate" and r.json()["is_active"] is True
    assert r.json()["email"] == "new.user@example.com" and r.json()["full_name"] == "New"
    # e-mails are case-insensitive: no duplicate account
    assert client.post("/api/auth/register", json={"email": "NEW.user@example.com", "password": PW}).status_code == 409
    # a role cannot be chosen at sign-up
    assert client.post("/api/auth/register", json={"email": "x@example.com", "password": PW, "role": "admin"}).json()["role"] == "candidate"


def test_login_and_me(client):
    register(client, "me@example.com")
    assert client.post("/api/auth/login", data={"username": "ME@example.com", "password": PW}).status_code == 200
    assert client.post("/api/auth/login", data={"username": "me@example.com", "password": "wrong-password-123"}).status_code == 401
    assert client.post("/api/auth/login", data={"username": "nobody@example.com", "password": PW}).status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"}).status_code == 401
    assert client.get("/api/auth/me").status_code == 401


def test_protected_routes_by_role(client, db):
    cand = make_user(db, client, "candidate", "cand@example.com")
    inter = make_user(db, client, "interviewer", "inter@example.com")
    direc = make_user(db, client, "direction", "dir@example.com")
    head = make_user(db, client, "iit_head", "head@example.com")
    admin = make_user(db, client, "admin", "admin@example.com")

    # anonymous: protected APIs need an account
    for path in ("/api/auth/me", "/api/admin/users", "/api/stats/overview", "/api/interviews/candidates", "/api/qcm/current"):
        assert client.get(path).status_code == 401, path
    # candidate journey is for candidates only
    for h in (inter, direc, head, admin):
        assert client.get("/api/auth/me/profile", headers=h).status_code == 403
        assert client.get("/api/appointments/me", headers=h).status_code == 403
    assert client.get("/api/auth/me/profile", headers=cand).status_code == 200
    # team areas
    assert client.get("/api/admin/users", headers=cand).status_code == 403
    assert client.get("/api/admin/users", headers=head).status_code == 403
    assert client.get("/api/admin/users", headers=admin).status_code == 200
    assert client.get("/api/stats/overview", headers=cand).status_code == 403
    assert client.get("/api/stats/overview", headers=inter).status_code == 403
    assert client.get("/api/stats/overview", headers=direc).status_code == 200
    assert client.get("/api/interviews/candidates", headers=cand).status_code == 403
    assert client.get("/api/interviews/candidates", headers=direc).status_code == 403
    assert client.get("/api/interviews/candidates", headers=inter).status_code == 200
    # the public catalogue and the chat stay open to visitors
    assert client.get("/api/programs").status_code == 200
    assert client.post("/api/conversations").status_code == 201


def test_admin_manages_accounts(client, db):
    admin = make_user(db, client, "admin", "root@example.com")
    r = client.post("/api/admin/users", headers=admin, json={"email": "Jury@Example.com", "password": PW, "full_name": "Jury", "role": "interviewer"})
    assert r.status_code == 201 and r.json()["role"] == "interviewer"
    uid = r.json()["id"]
    assert client.post("/api/admin/users", headers=admin, json={"email": "jury@example.com", "password": PW, "role": "direction"}).status_code == 409
    assert client.post("/api/admin/users", headers=admin, json={"email": "weak@example.com", "password": "short", "role": "direction"}).status_code == 422
    jury = login(client, "jury@example.com")
    assert client.get("/api/interviews/candidates", headers=jury).status_code == 200

    # role change takes effect on the next request (role is read from the database, not the token)
    assert client.patch(f"/api/admin/users/{uid}", headers=admin, json={"role": "direction"}).json()["role"] == "direction"
    assert client.get("/api/interviews/candidates", headers=jury).status_code == 403
    # suspension blocks login and existing tokens
    assert client.patch(f"/api/admin/users/{uid}", headers=admin, json={"is_active": False}).json()["is_active"] is False
    assert client.get("/api/auth/me", headers=jury).status_code == 403
    assert client.post("/api/auth/login", data={"username": "jury@example.com", "password": PW}).status_code == 403
    # password reset
    client.patch(f"/api/admin/users/{uid}", headers=admin, json={"is_active": True, "password": "a-brand-new-password"})
    assert client.post("/api/auth/login", data={"username": "jury@example.com", "password": "a-brand-new-password"}).status_code == 200
    assert client.patch("/api/admin/users/9999", headers=admin, json={"full_name": "x"}).status_code == 404


def test_last_admin_is_protected(client, db):
    admin = make_user(db, client, "admin", "only@example.com")
    me = client.get("/api/auth/me", headers=admin).json()
    assert client.patch(f"/api/admin/users/{me['id']}", headers=admin, json={"is_active": False}).status_code == 409
    r = client.patch(f"/api/admin/users/{me['id']}", headers=admin, json={"role": "direction"})
    assert r.status_code == 409 and "administrator" in r.json()["detail"]
    # with a second admin, the first one can step down
    second = client.post("/api/admin/users", headers=admin, json={"email": "second@example.com", "password": PW, "role": "admin"}).json()
    assert client.patch(f"/api/admin/users/{me['id']}", headers=admin, json={"role": "direction"}).status_code == 200
    assert second["role"] == "admin"
