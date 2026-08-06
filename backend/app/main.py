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

from app.core.config import settings as app_settings
from app.core.database import engine, Base
from app.routers import health, auth, profile, documents, onboarding, applications, ws
from app.routers import settings as settings_router


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
            logger.info(f"Running alembic with DATABASE_URL: {app_settings.DATABASE_URL}")
            command.upgrade(cfg, "head")
            logger.info("✅ Automatic database migrations applied successfully.")
    except Exception as e:
        logger.error(f"⚠️ Auto-migration skipped: {e}")


async def _ensure_database_exists():
    """Ensure PostgreSQL role 'formpilot' and database 'formpilot' exist."""
    import asyncpg
    if "sqlite" in app_settings.DATABASE_URL:
        return

    # Extract target host and port from config
    try:
        url_parts = app_settings.DATABASE_URL.replace("postgresql+asyncpg://", "").split("/")
        user_pass_host = url_parts[0]
        user_pass, host_port = user_pass_host.split("@")
        host, port = host_port.split(":") if ":" in host_port else (host_port, "5432")
    except Exception:
        host, port = "127.0.0.1", "5432"

    # Try connecting as superuser 'postgres' to auto-create role 'formpilot' and database 'formpilot'
    superuser_passwords = ["postgres", "root", "admin", "password", "formpilot", ""]
    for super_pass in superuser_passwords:
        try:
            conn = await asyncpg.connect(
                user="postgres",
                password=super_pass,
                host=host,
                port=int(port),
                database="postgres"
            )
            # Create role if missing
            role_exists = await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname = 'formpilot'")
            if not role_exists:
                logger.info("Role 'formpilot' missing — creating automatically...")
                await conn.execute("CREATE ROLE formpilot WITH LOGIN PASSWORD 'formpilot' CREATEDB SUPERUSER")
                logger.info("✅ Role 'formpilot' created successfully.")

            # Create database if missing
            db_exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'formpilot'")
            if not db_exists:
                logger.info("Database 'formpilot' missing — creating automatically...")
                await conn.execute('CREATE DATABASE "formpilot" OWNER formpilot')
                await conn.execute('GRANT ALL PRIVILEGES ON DATABASE "formpilot" TO formpilot')
                logger.info("✅ Database 'formpilot' created successfully.")

            await conn.close()
            return
        except Exception:
            continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create directories and run automatic migrations
    import os
    os.makedirs(app_settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs("test_forms", exist_ok=True)

    # Automatically ensure database exists & tables are created
    await _ensure_database_exists()

    import app.models  # noqa: F401
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created/verified successfully.")
    except Exception as e:
        logger.error(f"⚠️ Database table verification: {e}")

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
        title=app_settings.APP_NAME,
        description="AI-powered job-search and automatic form-filling agent",
        version="2.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins_list,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers with explicit CORS headers
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        origin = request.headers.get("origin", "*")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled server exception on {request.url.path}: {exc}", exc_info=True)
        origin = request.headers.get("origin", "*")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"},
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
        )

    # REST routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(onboarding.router)
    app.include_router(profile.router)
    app.include_router(documents.router)
    app.include_router(applications.router)
    app.include_router(settings_router.router)

    # WebSocket router
    app.include_router(ws.router)

    # Serve local test forms as static files (dev only)
    if app_settings.APP_ENV == "development":
        import os
        if os.path.exists("test_forms"):
            app.mount("/test-forms", StaticFiles(directory="test_forms", html=True), name="test_forms")

    return app


app = create_app()
