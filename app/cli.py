"""Local administration commands.

    python -m app.cli init-db             create missing tables + base catalogue
    python -m app.cli seed-demo           add the demo data (accounts for every role, candidates, catalogue)
    python -m app.cli reset-db --yes      DELETE all data and recreate the schema (add --demo to reseed)
    python -m app.cli create-admin --email you@example.com --name "Your Name"   (asks for the password)
    python -m app.cli purge-guests        expire / delete old visitor sessions now
    python -m app.cli check               show the configuration in use and schema status
    python -m app.cli init-env            create .env from .env.example with a random SECRET_KEY (if .env is absent)
"""

import argparse
import getpass
import sys

from sqlalchemy import func, select

from app.core.config import settings
from app.db.session import SessionLocal, create_tables, drop_tables, engine, schema_problems


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
        import re
        import secrets
        from pathlib import Path

        env, example = Path(".env"), Path(".env.example")
        if env.exists():
            print(".env already exists: left unchanged.")
            return 0
        text = example.read_text(encoding="utf-8")
        text = re.sub(r"^SECRET_KEY=.*$", "SECRET_KEY=" + secrets.token_urlsafe(48), text, flags=re.M)
        env.write_text(text, encoding="utf-8")
        print(".env created with a random SECRET_KEY.")
        return 0

    if args.cmd == "check":
        url = settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url
        print(f"env={settings.env}  database={url}  demo_data={settings.seed_demo_data}")
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
