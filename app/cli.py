"""Local administration commands.

    python -m app.cli init-db             create missing tables + base catalogue
    python -m app.cli seed-demo           add the demo data (accounts for every role, candidates, catalogue)
    python -m app.cli reset-db --yes      DELETE all data and recreate the schema (add --demo to reseed)
    python -m app.cli create-admin --email you@example.com --name "Your Name"   (asks for the password)
    python -m app.cli purge-guests        expire / delete old visitor sessions now
    python -m app.cli check               show the configuration in use and schema status
    python -m app.cli init-env            create .env with a random SECRET_KEY (if .env is absent)
"""

import argparse
import getpass
import sys

from sqlalchemy import func, select

from app.core.config import settings
from app.db.session import (
    DatabaseUnavailableError,
    SessionLocal,
    check_connection,
    create_tables,
    drop_tables,
    engine,
    schema_problems,
    vector_available,
)


# Content of a new .env (init-env). SECRET_KEY is generated; adjust DATABASE_URL to your PostgreSQL.
ENV_TEMPLATE = """# SmartCampus backend — local configuration, created by `python -m app.cli init-env` (never committed). Every value has a safe default for local development.

APP_NAME=SmartCampus AI
# dev: tables created on startup (+ base catalogue) · test · prod
ENV=dev

# Database — PostgreSQL: user, password, host, port, database (see GUIDE_DEMARRAGE.md, section 2).
# pgvector is used when the server provides it (RAG table); otherwise that table is skipped.
DATABASE_URL=postgresql+psycopg://smartcampus:smartcampus@localhost:5432/smartcampus

# JWT signing key: a random string of at least 32 characters, never committed.
# Generate one with:  python -c "import secrets; print(secrets.token_urlsafe(48))"
SECRET_KEY={secret_key}
ACCESS_TOKEN_EXPIRE_MINUTES=60
PASSWORD_MIN_LENGTH=12

# Frontend origin(s) allowed to call the API (comma-separated). The Vite dev server proxies /api, so this only
# matters if the frontend calls the API directly from another origin.
CORS_ORIGINS=http://localhost:3000

# Demo data (one account per role, candidates, catalogue) added on startup when absent. Local only.
SEED_DEMO_DATA=true

# Uploaded candidate documents
UPLOAD_DIR=uploads
MAX_UPLOAD_BYTES=10485760

# Visitor (guest) chat sessions
GUEST_IDLE_MINUTES=30
GUEST_MAX_HOURS=24
GUEST_MAX_MESSAGES=40
GUEST_MAX_CONVERSATIONS=3
GUEST_MESSAGES_PER_MINUTE=8
GUEST_SESSIONS_PER_HOUR_PER_CLIENT=20
GUEST_MESSAGE_MAX_CHARS=1000
GUEST_PURGE_INTERVAL_MINUTES=15
GUEST_RETENTION_HOURS=24

# RAG embeddings size (pgvector)
EMBEDDING_DIM=768
"""


def _init() -> None:
    from app.seed import seed_programs

    create_tables(engine)
    with SessionLocal() as db:
        seed_programs(db)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m app.cli", description="SmartCampus backend: local administration")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-db")
    sub.add_parser("seed-demo")
    r = sub.add_parser("reset-db")
    r.add_argument("--yes", action="store_true", help="confirm: every row is deleted")
    r.add_argument("--demo", action="store_true", help="reseed the demo data afterwards")
    a = sub.add_parser("create-admin")
    a.add_argument("--email", required=True)
    a.add_argument("--name", default="")
    a.add_argument("--password", help="avoid on shared machines (shell history); prompted when omitted")
    sub.add_parser("purge-guests")
    sub.add_parser("check")
    sub.add_parser("init-env")
    args = p.parse_args(argv)

    if args.cmd == "init-env":
        import secrets
        from pathlib import Path

        env = Path(".env")
        if env.exists():
            print(".env already exists: left unchanged.")
            return 0
        env.write_text(ENV_TEMPLATE.format(secret_key=secrets.token_urlsafe(48)), encoding="utf-8")
        print(".env created with a random SECRET_KEY (edit DATABASE_URL if your PostgreSQL differs).")
        return 0

    try:
        check_connection()
    except DatabaseUnavailableError as e:
        print(e)
        return 1

    if args.cmd == "check":
        url = settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url
        print(f"env={settings.env}  database={url}  demo_data={settings.seed_demo_data}")
        if engine.dialect.name == "postgresql":
            print("pgvector: " + ("available (RAG table enabled)" if vector_available(engine) else "not installed (RAG table skipped)"))
        problems = schema_problems(engine)
        print("schema: OK" if not problems else "schema outdated -> " + "; ".join(problems))
        return 0 if not problems else 1

    if args.cmd == "reset-db":
        if not args.yes:
            print("Refused: this deletes every row. Re-run with --yes to confirm.")
            return 2
        drop_tables(engine)
        _init()
        print("Database recreated.")
        if args.demo:
            from app.demo_data import seed_demo

            with SessionLocal() as db:
                seed_demo(db)
            print("Demo data added (see GUIDE_DEMARRAGE.md for the accounts).")
        return 0

    problems = schema_problems(engine)
    if problems:
        print("Outdated schema (" + "; ".join(problems) + "). Run: python -m app.cli reset-db --yes --demo")
        return 1

    if args.cmd == "init-db":
        _init()
        print("Tables ready, base catalogue added.")
    elif args.cmd == "seed-demo":
        _init()
        from app.demo_data import seed_demo

        with SessionLocal() as db:
            print("Demo data added." if seed_demo(db) else "Demo data already present: nothing to do.")
    elif args.cmd == "create-admin":
        from app.api.routes.auth import email_taken, normalize_email
        from app.core.security import hash_password
        from app.models.models import Role, User

        pw = args.password or getpass.getpass("Password (min %d characters): " % settings.password_min_length)
        if len(pw) < settings.password_min_length:
            print(f"Password too short (min {settings.password_min_length} characters).")
            return 2
        _init()
        with SessionLocal() as db:
            if email_taken(db, args.email):
                print("An account already uses this e-mail.")
                return 2
            db.add(User(email=normalize_email(args.email), full_name=args.name, role=Role.admin, hashed_password=hash_password(pw)))
            db.commit()
            print(f"Administrator created: {normalize_email(args.email)} ({db.scalar(select(func.count()).select_from(User).where(User.role == Role.admin))} admin(s) in total)")
    elif args.cmd == "purge-guests":
        from app.services.guest import purge_expired

        with SessionLocal() as db:
            print(purge_expired(db))
    return 0


if __name__ == "__main__":
    sys.exit(main())
