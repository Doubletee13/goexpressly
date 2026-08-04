from __future__ import annotations
"""
app/main.py — FastAPI application factory.

The `lifespan` context manager runs once on startup/shutdown:
  - Imports all models so SQLAlchemy's metadata is fully populated
  - Calls create_all() to create any missing tables (idempotent, never drops)

Routers are registered here; each router handles its own URL prefix.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure all DB tables exist. Shutdown: (nothing needed)."""
    # Import all models to register them with Base.metadata before create_all
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup on shutdown (engine connection pool closes automatically)


def create_app() -> FastAPI:
    application = FastAPI(
        title="GoExpressly — Courier Tracking API",
        description=(
            "Backend API for the GoExpressly courier and package tracking platform. "
            "Supports admin authentication, shipment management, tracking history, "
            "and a public unauthenticated tracking lookup."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — restrict in production to your actual frontend origin
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Tighten this before exposing to the internet
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────────────────────────
    from app.routers.health import router as health_router

    application.include_router(health_router)

    from app.routers.auth import router as auth_router
    application.include_router(auth_router)

    from app.routers.packages import router as packages_router
    application.include_router(packages_router)

    from app.routers.events import router as events_router
    application.include_router(events_router)

    from app.routers.tracking import router as tracking_router
    application.include_router(tracking_router)

    return application


app = create_app()
