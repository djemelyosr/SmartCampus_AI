import os

os.environ.setdefault("ENV", "test")  # keep the app lifespan from touching PostgreSQL

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import create_tables, get_db
from app import models as _models  # noqa: F401  (register all tables)
from app.main import app as api


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """API on an in-memory SQLite DB (pgvector table excluded) and a temp upload dir."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    create_tables(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        with Session() as db:
            yield db

    api.dependency_overrides[get_db] = override
    yield TestClient(api)
    api.dependency_overrides.clear()


def register(client, email: str, password: str = "a-long-test-password", name: str = "Test User") -> dict:
    assert client.post("/api/auth/register", json={"email": email, "password": password, "full_name": name}).status_code == 201
    tok = client.post("/api/auth/login", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture()
def auth(client):
    """Registered + logged-in candidate; returns auth headers."""
    return register(client, "test.candidate@example.com")


@pytest.fixture()
def program(client):
    """A catalogue programme inserted directly (the creation endpoint needs a head role)."""
    from app.models.models import Institution, Level, Program

    db = next(api.dependency_overrides[get_db]())
    p = Program(institution=Institution.IIT, level=Level.licence, name="Licence en informatique")
    db.add(p)
    db.commit()
    return p.id


PW = "a-long-test-password"


@pytest.fixture()
def db(client):
    """A session on the same in-memory database as the API."""
    return next(api.dependency_overrides[get_db]())


def login(client, email: str, password: str = PW) -> dict:
    r = client.post("/api/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_user(db, client, role: str, email: str, password: str = PW, name: str = "") -> dict:
    """Account with any role, created directly in the database (team roles cannot self-register)."""
    from app.core.security import hash_password
    from app.models.models import CandidateProfile, Role, User

    u = User(email=email, full_name=name or email.split("@")[0], role=Role(role), hashed_password=hash_password(password))
    if role == "candidate":
        u.profile = CandidateProfile(consent_given=True)
    db.add(u)
    db.commit()
    return login(client, email, password)
