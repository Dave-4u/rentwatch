from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.database import Base, engine, SessionLocal
import backend.app.models  # noqa: F401 — register metadata
from backend.app.routers import admin, auth, dashboard, leases, notifications, payments, properties
from backend.app.seed import ensure_landlord
from backend.app.db_migrate import ensure_schema
from backend.app.services.overdue_runner import check_and_notify_overdue

DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_schema(engine)
    db = SessionLocal()
    try:
        ensure_landlord(db)
        check_and_notify_overdue(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

_origins = settings.cors_origin_list
_allow_credentials = "*" not in _origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_allow_credentials,
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


def _mount_spa() -> None:
    """Serve Vite production build from the same origin when frontend/dist exists."""
    if not DIST_DIR.is_dir():
        return
    assets = DIST_DIR / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/")
    async def spa_root():
        return FileResponse(DIST_DIR / "index.html")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        candidate = DIST_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")


_mount_spa()
