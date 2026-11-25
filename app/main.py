
import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    admin_users, admission_conditions, appointments, auth, conversations, curricula, documents, fees, health, interviews,
    official_info, payment_terms, preinscriptions, programs, qcm, specialties, stats, subjects,
)
from app.core.config import settings
from app.db.session import SessionLocal, init_db
from app.services import session_memory

log = logging.getLogger("smartcampus")


def _purge_session_memories() -> None:
    try:
        with SessionLocal() as db:
            n = session_memory.purge_expired(db)
        if n:
            log.info("session memory: %d expired memories purged", n)
    except Exception:  # never let housekeeping stop the API
        log.exception("session memory purge failed")


async def _purge_loop() -> None:
    while True:
        await asyncio.sleep(settings.session_purge_interval_seconds)
        await asyncio.to_thread(_purge_session_memories)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.env == "dev":
        init_db()
    task = None
    if settings.env != "test":  # tests run on SQLite and must not touch PostgreSQL
        _purge_session_memories()
        task = asyncio.create_task(_purge_loop())
    yield
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],  # total of a paginated catalogue search
)

app.include_router(health.router)
for r in (
    auth.router, admin_users.router, programs.router, specialties.router, curricula.router, subjects.router,
    admission_conditions.router, fees.router, payment_terms.router, official_info.router, conversations.router,
    preinscriptions.router, qcm.router, appointments.router, documents.router, stats.router, interviews.router,
):
    app.include_router(r, prefix="/api")
