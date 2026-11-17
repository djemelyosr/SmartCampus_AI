from collections.abc import Iterator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base

IS_SQLITE = settings.database_url.startswith("sqlite")

if IS_SQLITE:
    # Local, zero-install mode: a single file. Threads are fine since each request has its own session.
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")
else:
    engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# Tables that only exist on PostgreSQL (pgvector). The RAG index is not available in SQLite mode.
POSTGRES_ONLY_TABLES = {"document_chunks"}


def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db


def create_tables(bind: Engine) -> None:
    """Create the schema on PostgreSQL (with pgvector) or SQLite (without the vector tables)."""
    import app.models  # noqa: F401  (register tables)

    if bind.dialect.name == "sqlite":
        tables = [t for n, t in Base.metadata.tables.items() if n not in POSTGRES_ONLY_TABLES]
        Base.metadata.create_all(bind, tables=tables)
        return
    with bind.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind)


def init_db() -> None:
    from app.seed import seed_programs

    create_tables(engine)
    with SessionLocal() as db:
        seed_programs(db)
