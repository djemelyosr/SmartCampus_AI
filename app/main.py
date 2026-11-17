from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import appointments, auth, conversations, documents, health, preinscriptions, programs, qcm
from app.core.config import settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.env == "dev":
        init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
for r in (auth.router, programs.router, conversations.router, preinscriptions.router, qcm.router, appointments.router, documents.router):
    app.include_router(r, prefix="/api")
