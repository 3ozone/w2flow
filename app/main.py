"""FastAPI application entry point."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.infrastructure.api.v1.routers import (
    filters_router,
    health_router,
    pipeline_router,
    reports_router,
    tenders_router,
    ui_router,
)
from app.infrastructure import dependencies

logging.basicConfig(
    level=logging.DEBUG if settings.app_debug else logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)

_BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="w2flow",
    description="Automated public tender monitoring and scoring API.",
    version="1.0.0",
)

# Static files and templates
app.mount("/static", StaticFiles(directory=_BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=_BASE_DIR / "templates")

_PREFIX = "/api/v1"

# Inject shared repository into routers that need it
tenders_router._repository = dependencies.repository

app.include_router(filters_router.router, prefix=_PREFIX)
app.include_router(health_router.router, prefix=_PREFIX)
app.include_router(tenders_router.router, prefix=_PREFIX)
app.include_router(reports_router.router, prefix=_PREFIX)
app.include_router(pipeline_router.router, prefix=_PREFIX)
app.include_router(ui_router.router)  # UI pages — no /api/v1 prefix
