import os

os.environ.setdefault("ENV", "test")  # keep the app lifespan from touching the development database

# Tests run on PostgreSQL, in a DEDICATED database (every table is emptied before each test). Create it once:
#   CREATE DATABASE smartcampus_test OWNER smartcampus;
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://smartcampus:smartcampus@localhost:5432/smartcampus_test"
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import close_all_sessions, sessionmaker

from app.db.session import DatabaseUnavailableError, check_connection, create_tables, drop_tables, get_db, _tables_for
from app import models as _models  # noqa: F401  (register all tables)
from app.main import app as api


@pytest.fixture(scope="session")
def engine():
    """Test database, schema recreated once per test run."""
    eng = create_engine(TEST_DATABASE_URL)
    try:
        check_connection(eng)
    except DatabaseUnavailableError as e:
        pytest.exit(f"{e} Tests need the test database: see GUIDE_DEMARRAGE.md (tests).", returncode=1)
    drop_tables(eng)
    create_tables(eng)
    yield eng
    close_all_sessions()
    eng.dispose()


@pytest.fixture()
def client(engine, tmp_path, monkeypatch):
    """API on an empty test database and a temp upload dir."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    close_all_sessions()  # sessions left open by the previous test would block TRUNCATE
    with engine.begin() as conn:
        names = ", ".join(f'"{t.name}"' for t in _tables_for(engine))
        conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        with Session() as db:
            yield db

    api.dependency_overrides[get_db] = override
    yield TestClient(api)
    api.dependency_overrides.clear()
    close_all_sessions()


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
