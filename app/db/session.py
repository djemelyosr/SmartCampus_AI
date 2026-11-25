import sqlite3
from collections.abc import Iterator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base


@event.listens_for(Engine, "connect")
def _sqlite_translate(dbapi_conn, _record) -> None:
    """SQLite (unit tests only) has no translate(): register it so the accent-insensitive catalogue search runs there too."""
    if isinstance(dbapi_conn, sqlite3.Connection):
        dbapi_conn.create_function(
            "translate", 3, lambda s, a, b: None if s is None else str(s).translate(str.maketrans(a, b)), deterministic=True
        )


# PostgreSQL only: the application no longer ships a file-based (SQLite) database.
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# Tables that need the pgvector extension (RAG index).
POSTGRES_ONLY_TABLES = {"document_chunks"}


def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db


def create_tables(bind: Engine) -> None:
    """Create the schema on PostgreSQL (with pgvector when available).

    The in-memory SQLite branch only serves the unit tests (no persisted database).
    """
    import app.models  # noqa: F401  (register tables)

    if bind.dialect.name == "sqlite":
        tables = [t for n, t in Base.metadata.tables.items() if n not in POSTGRES_ONLY_TABLES]
        Base.metadata.create_all(bind, tables=tables)
        return
    try:
        with bind.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    except Exception:
        # PostgreSQL without pgvector (e.g. postgres:16-alpine): create everything except the vector tables.
        tables = [t for n, t in Base.metadata.tables.items() if n not in POSTGRES_ONLY_TABLES]
        Base.metadata.create_all(bind, tables=tables)
        _migrate(bind)
        return
    Base.metadata.create_all(bind)
    _migrate(bind)


def _migrate(bind: Engine) -> None:
    """Tiny additive migrations for databases created before a column existed (no Alembic yet)."""
    if bind.dialect.name != "postgresql":
        return
    with bind.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"))
        # Access requests: accounts that existed before are approved (they could already sign in).
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS requested_role VARCHAR(20)"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS approval_status VARCHAR(16) NOT NULL DEFAULT 'approved'"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reviewed_by_id INTEGER REFERENCES users(id)"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS review_note VARCHAR(500)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_approval_status ON users (approval_status)"))
        # Blocked accounts (distinct from inactive ones): reason, date and administrator are kept.
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN NOT NULL DEFAULT FALSE"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS blocked_reason VARCHAR(500)"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS blocked_at TIMESTAMPTZ"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS blocked_by_id INTEGER REFERENCES users(id)"))
        # Official information (publication status + validity period). Items entered before this existed were already
        # visible to candidates, so they are backfilled as published; new items start as drafts (ORM default).
        for table in ("fees", "admission_conditions"):
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS status VARCHAR(16) NOT NULL DEFAULT 'published'"))
            conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN status DROP DEFAULT"))
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS valid_from DATE"))
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS valid_until DATE"))
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS academic_year VARCHAR(9)"))
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ"))
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS published_by_id INTEGER REFERENCES users(id)"))
            conn.execute(text(f"UPDATE {table} SET published_at = created_at WHERE status = 'published' AND published_at IS NULL"))
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_{table}_status ON {table} (status)"))


def init_db() -> None:
    from app.seed import seed_programs, seed_team_accounts
    from app.seed_catalog import seed_catalog

    create_tables(engine)
    with SessionLocal() as db:
        seed_programs(db)
        seed_catalog(db)
        seed_team_accounts(db)
