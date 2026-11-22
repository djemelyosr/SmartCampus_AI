import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    admin_users,
    appointments,
    auth,
    catalog,
    conversations,
    documents,
    guest,
    health,
    interviews,
    preinscriptions,
    qcm,
    stats,
)
from app.core.config import settings
from app.db.session import SessionLocal, init_db
from app.services import guest as guest_service

log = logging.getLogger("smartcampus")


def _purge_once() -> None:
    with SessionLocal() as db:
        res = guest_service.purge_expired(db)
        if res["expired"] or res["deleted"]:
            log.info("visitor sessions: %s expired, %s deleted", res["expired"], res["deleted"])


async def _purge_loop() -> None:
    """Expire and clean up visitor sessions periodically."""
    while True:
        try:
            await run_in_threadpool(_purge_once)
        except Exception:  # never let the clean-up kill the app
            log.exception("visitor session clean-up failed")
        await asyncio.sleep(settings.guest_purge_interval_minutes * 60)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = None
    if settings.env == "dev":
        init_db()
    if settings.env != "test":
        task = asyncio.create_task(_purge_loop())
    yield
    if task:
        task.cancel()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[guest_service.HEADER],
)

app.include_router(health.router)
for r in (
    auth.router,
    admin_users.router,
    catalog.router,
    conversations.router,
    guest.router,
    preinscriptions.router,
    qcm.router,
    appointments.router,
    documents.router,
    stats.router,
    interviews.router,
):
    app.include_router(r, prefix="/api")
