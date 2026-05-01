"""FastAPI application entry point."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.config import settings
from app.infrastructure.api.v1.routers import (
    filters_router,
    pipeline_router,
    reports_router,
    tenders_router,
)
from app.infrastructure import dependencies

logging.basicConfig(
    level=logging.DEBUG if settings.app_debug else logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)

app = FastAPI(
    title="w2flow",
    description="Automated public tender monitoring and scoring API.",
    version="0.4.0",
)

_PREFIX = "/api/v1"

# Inject shared repository into routers that need it
tenders_router._repository = dependencies.repository

app.include_router(filters_router.router, prefix=_PREFIX)
app.include_router(tenders_router.router, prefix=_PREFIX)
app.include_router(reports_router.router, prefix=_PREFIX)
app.include_router(pipeline_router.router, prefix=_PREFIX)
