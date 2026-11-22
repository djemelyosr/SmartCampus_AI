from collections.abc import Iterator
from functools import cache

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base

# The database is PostgreSQL (driver psycopg 3), configured by DATABASE_URL.
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# Tables that need the pgvector extension (RAG index). Skipped when the extension is not installed on the server.
VECTOR_TABLES = {"document_chunks"}


class OutdatedSchemaError(RuntimeError):
    pass


class DatabaseUnavailableError(RuntimeError):
    pass


def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db


@cache
def _vector_available(url: str) -> bool:
    with create_engine(url).connect() as conn:
        return conn.execute(text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")).first() is not None


def vector_available(bind: Engine) -> bool:
    """True when the PostgreSQL server can provide the pgvector extension."""
    return _vector_available(bind.url.render_as_string(hide_password=False))


def _tables_for(bind: Engine) -> list:
    import app.models  # noqa: F401  (register tables)

    if vector_available(bind):
        return list(Base.metadata.tables.values())
    return [t for n, t in Base.metadata.tables.items() if n not in VECTOR_TABLES]


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
    """Create the schema; enable pgvector first when the server provides it."""
    if vector_available(bind):
        with bind.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind, tables=_tables_for(bind))


def drop_tables(bind: Engine) -> None:
    Base.metadata.drop_all(bind, tables=[t for t in _tables_for(bind) if t.name in inspect(bind).get_table_names()])


def check_connection(bind: Engine = engine) -> None:
    """Fail early with a readable message when PostgreSQL cannot be reached."""
    try:
        with bind.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as e:
        where = bind.url.render_as_string(hide_password=True)
        raise DatabaseUnavailableError(
            f"Impossible de se connecter à PostgreSQL ({where}). Vérifiez que le serveur est démarré, que la base et "
            "l'utilisateur existent, et la valeur de DATABASE_URL dans backend/.env (voir GUIDE_DEMARRAGE.md). "
            f"Détail : {str(e.orig).strip().splitlines()[0] if e.orig else e}"
        ) from None


def init_db() -> None:
    """Startup in dev: check the schema, create missing tables, add the base catalogue (and demo data if enabled)."""
    from app.seed import seed_programs

    check_connection()
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
