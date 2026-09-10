from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import Base, engine, SessionLocal
import backend.app.models  # noqa: F401 — register metadata
from backend.app.routers import admin, auth, dashboard, leases, notifications, payments, properties
from backend.app.seed import ensure_landlord
from backend.app.services.overdue_runner import check_and_notify_overdue


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_landlord(db)
        check_and_notify_overdue(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(properties.router)
app.include_router(leases.router)
app.include_router(payments.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
