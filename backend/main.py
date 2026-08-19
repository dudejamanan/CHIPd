"""
Silica EDA Platform
====================

FastAPI application entry point.

Run locally with:

    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

Or:

    python -m backend.main

No Docker is required.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import design, projects
from backend.config import settings
from backend.models.database import init_db


# ============================================================================
# Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger(
    "silica"
)


# ============================================================================
# Application
# ============================================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-assisted Electronic Design Automation "
        "platform for RTL generation, verification "
        "and automated repair."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# CORS
# ============================================================================

# Convert configured origins into a clean list.
#
# During local development this should normally contain:
#
#     http://localhost:3000
#
# and optionally:
#
#     http://127.0.0.1:3000
#
#
# We intentionally do NOT use allow_origins=["*"] together with
# allow_credentials=True.
#
# Explicit origins make browser behavior predictable.
configured_origins = settings.cors_origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
)


# ============================================================================
# Routers
# ============================================================================

app.include_router(
    projects.router,
    prefix="/projects",
)

app.include_router(
    design.router,
    prefix="/design",
)


# ============================================================================
# Startup
# ============================================================================


@app.on_event("startup")
async def startup_event() -> None:
    """
    Initialize local application resources.
    """

    logger.info(
        "Starting %s v%s",
        settings.app_name,
        settings.app_version,
    )

    logger.info(
        "Initializing SQLite database..."
    )

    init_db()

    logger.info(
        "Database initialized."
    )

    logger.info(
        "CORS origins: %s",
        configured_origins,
    )

    logger.info(
        "Silica backend ready."
    )


# ============================================================================
# Root
# ============================================================================


@app.get(
    "/",
    tags=["System"],
)
async def root() -> dict[str, object]:
    """
    API root endpoint.
    """

    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "description": (
            "AI-assisted EDA platform"
        ),
        "docs": "/docs",
    }


# ============================================================================
# Health
# ============================================================================


@app.get(
    "/health",
    tags=["System"],
)
async def health_check() -> dict[str, object]:
    """
    Health endpoint used by the frontend and local development.
    """

    return {
        "status": "healthy",
        "service": "silica-backend",
        "version": settings.app_version,
    }


# ============================================================================
# Development entry point
# ============================================================================


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )