"""Punt d'entrada de l'aplicació FastAPI — w2flow.

Registra els routers, els exception handlers i els fitxers estàtics.
Tota la lògica de negoci viu als use cases i al domini; main.py
és exclusivament configuració i cablejat.
"""
import logging

import structlog

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.application.exceptions.application_errors import NoActiveFilterConfigError, TenderApiError
from app.config import Settings
from app.infrastructure.api.exception_handlers import (
    generic_error_handler,
    no_active_filter_config_handler,
    tender_api_error_handler,
)
from app.infrastructure.api.filters_router import router as filters_router
from app.infrastructure.api.pipeline_router import router as pipeline_router
from app.infrastructure.api.tenders_router import router as tenders_router
from app.infrastructure.api.documents_router import router as documents_router
from app.infrastructure.api.ui_router import router as ui_router

_settings = Settings()

logging.basicConfig(
    level=logging.DEBUG if _settings.app_debug else logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)

# Timbal emet logs molt verbosos internament; només mostrem WARNING i superiors.
for _noisy in ("timbal", "timbal.agent", "timbal.state", "httpx", "httpcore"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

# Timbal usa structlog internament — silenciem debug/info del seu bound logger.
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING),
)

app = FastAPI(
    title="w2flow",
    description="Monitoratge automatitzat i puntuació de licitacions públiques.",
    version="0.3.0",
)

# ---------------------------------------------------------------------------
# Fitxers estàtics
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

app.add_exception_handler(NoActiveFilterConfigError,
                          no_active_filter_config_handler)
app.add_exception_handler(TenderApiError, tender_api_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(ui_router)
app.include_router(pipeline_router)
app.include_router(filters_router)
app.include_router(tenders_router)
app.include_router(documents_router)
