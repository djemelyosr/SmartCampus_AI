from app.core.security import hash_password
from app.db.session import get_db
from app.main import app as api
from app.models.models import Role, User


def test_profile_is_404_for_staff_and_200_for_candidates(client, auth):
    assert client.get("/api/auth/me/profile", headers=auth).status_code == 200  # candidates get a profile at registration
    db = next(api.dependency_overrides[get_db]())
    db.add(User(email="admin.profile@example.com", full_name="Admin", role=Role.admin, hashed_password=hash_password("a-long-test-password")))
    db.commit()
    tok = client.post("/api/auth/login", data={"username": "admin.profile@example.com", "password": "a-long-test-password"}).json()["access_token"]
    r = client.get("/api/auth/me/profile", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 404  # no more "500 Internal Server Error" on /espace/profil for admins
