from __future__ import annotations

from contextlib import asynccontextmanager
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.routers import health, auth, profile, documents, onboarding, applications, ws


def _run_auto_migrations():
    """Run Alembic database migrations automatically on application startup."""
    import os
    try:
        from alembic.config import Config
        from alembic import command
        # Locate alembic.ini in backend root
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_ini = os.path.join(backend_dir, "alembic.ini")
        if os.path.exists(alembic_ini):
            cfg = Config(alembic_ini)
            cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
            logger.info(f"Running alembic with DATABASE_URL: {settings.DATABASE_URL}")
            command.upgrade(cfg, "head")
            logger.info("✅ Automatic database migrations applied successfully.")
    except Exception as e:
        logger.error(f"⚠️ Auto-migration skipped: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create directories and run automatic migrations
    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs("test_forms", exist_ok=True)

    # Automatically run migrations on startup
    _run_auto_migrations()

    yield
    # Shutdown — close all Playwright browser contexts
    try:
        from app.browser.manager import BrowserManager
        await BrowserManager.shutdown()
    except Exception:
        pass
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-powered job-search and automatic form-filling agent",
        version="2.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # REST routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(onboarding.router)
    app.include_router(profile.router)
    app.include_router(documents.router)
    app.include_router(applications.router)

    # WebSocket router
    app.include_router(ws.router)

    # Serve local test forms as static files (dev only)
    if settings.APP_ENV == "development":
        import os
        if os.path.exists("test_forms"):
            app.mount("/test-forms", StaticFiles(directory="test_forms", html=True), name="test_forms")

    return app


app = create_app()
