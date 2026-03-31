"""Application entrypoint for the trading control plane."""

import logging
from contextlib import asynccontextmanager

import nest_asyncio
from fastapi import FastAPI

try:
    nest_asyncio.apply()
except ValueError:
    # uvloop cannot be patched; continue with the active event loop.
    pass

from app.api.router import api_router
from app.bootstrap import initialize_database_schema, seed_demo_data
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.settings import Settings, get_settings
from app.db.session import SessionLocal
from app.middleware.request_context import RequestContextMiddleware
from app.ui.router import router as ui_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def application_lifespan(app: FastAPI):
    """Run startup bootstrap and graceful shutdown tasks using FastAPI's lifespan API."""
    settings: Settings = get_settings()
    logger.info("Application startup initiated", extra={"environment": settings.environment})
    bootstrap_mode = initialize_database_schema(settings)
    session = SessionLocal()
    try:
        seeded = seed_demo_data(settings, session)
    finally:
        session.close()
    logger.info(
        "Application startup bootstrap completed",
        extra={"bootstrap_mode": bootstrap_mode, "seeded_demo_data": seeded},
    )
    yield
    logger.info("Application shutdown completed")


def create_application() -> FastAPI:
    """Build and configure the FastAPI application used by local and production servers."""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=application_lifespan,
    )
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)
    app.include_router(ui_router)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_application()
