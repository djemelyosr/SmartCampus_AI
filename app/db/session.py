from collections.abc import Iterator

from sqlalchemy import create_engine, event, inspect, text
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


class OutdatedSchemaError(RuntimeError):
    pass


def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db


def _tables_for(bind: Engine) -> list:
    import app.models  # noqa: F401  (register tables)

    if bind.dialect.name == "sqlite":
        return [t for n, t in Base.metadata.tables.items() if n not in POSTGRES_ONLY_TABLES]
    return list(Base.metadata.tables.values())


def schema_problems(bind: Engine) -> list[str]:
    """Existing tables that miss columns of the current models (database created by an older version)."""
    insp = inspect(bind)
    existing = set(insp.get_table_names())
    problems = []
    for t in _tables_for(bind):
        if t.name in existing:
            have = {c["name"] for c in insp.get_columns(t.name)}
            missing = [c.name for c in t.columns if c.name not in have]
            if missing:
                problems.append(f"{t.name}: {', '.join(missing)}")
    return problems


def create_tables(bind: Engine) -> None:
    """Create the schema on PostgreSQL (with pgvector) or SQLite (without the vector tables)."""
    if bind.dialect.name != "sqlite":
        with bind.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind, tables=_tables_for(bind))


def drop_tables(bind: Engine) -> None:
    Base.metadata.drop_all(bind, tables=[t for t in _tables_for(bind) if t.name in inspect(bind).get_table_names()])


def init_db() -> None:
    """Startup in dev: check the schema, create missing tables, add the base catalogue (and demo data if enabled)."""
    from app.seed import seed_programs

    problems = schema_problems(engine)
    if problems:
        raise OutdatedSchemaError(
            "La base de données a été créée par une ancienne version (colonnes manquantes : "
            + "; ".join(problems)
            + "). Réinitialisez-la avec :  python -m app.cli reset-db --yes --demo"
        )
    create_tables(engine)
    with SessionLocal() as db:
        seed_programs(db)
        if settings.seed_demo_data:
            from app.demo_data import seed_demo

            seed_demo(db)
