"""Router FastAPI para las páginas HTML de la interfaz de usuario (RF-07).

Sirve los templates Jinja2 con Tailwind + HTMX. No contiene lógica de negocio:
delega a use cases y repositorios existentes.

Rutas HTML:
  GET  /                           → index.html (dashboard + botón pipeline)
  GET  /licitacions                → tenders.html (lista de licitaciones puntuadas)
  GET  /filtres                    → filters.html (formulario de configuración)
  POST /pipeline/trigger           → lanza el pipeline en background, devuelve partial de estado
  GET  /partials/pipeline-status   → partials/pipeline_status.html (polling HTMX)
  GET  /partials/search-results    → partials/search_results.html (resultados última ejecución)
"""
import json
import threading
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.application.dtos.report_dto import ReportDTO
from app.application.exceptions.application_errors import NoActiveFilterConfigError
from app.infrastructure.database import SessionLocal
from app.infrastructure.dependencies import (
    get_db,
    get_filter_repository,
    get_run_pipeline_use_case,
    get_tender_document_repository,
    get_tender_repository,
)
from app.infrastructure.models.tender_model import TenderModel

router = APIRouter(tags=["ui"])

_templates = Jinja2Templates(
    directory=Path(__file__).resolve().parents[2] / "templates"
)
_templates.env.filters["fromjson"] = json.loads

# ---------------------------------------------------------------------------
# Estado en memoria del pipeline (thread-safe, RNF-01, RNF-03, RNF-04)
# ---------------------------------------------------------------------------

_state_lock = threading.Lock()

_pipeline_state: dict[str, Any] = {
    "state": "idle",   # idle | running | completed | failed
    "total": 0,
    "downloaded": 0,
    "skipped": 0,
    "failed": 0,
    "error": None,
}

_last_report: ReportDTO | None = None


def _pipeline_state_context() -> dict[str, Any]:
    """Devuelve una copia del estado actual del pipeline para pasar al template."""
    with _state_lock:
        return dict(_pipeline_state)


def _run_pipeline_task(config: Any) -> None:
    """Ejecuta el pipeline en un hilo background y actualiza el estado en memoria."""
    global _last_report

    db = SessionLocal()
    try:
        use_case = get_run_pipeline_use_case(db)
        report = use_case.execute(config=config, today=date.today())

        db.commit()
        with _state_lock:
            _last_report = report
            _pipeline_state.update({
                "state": "completed",
                "total": len(report.tenders),
                "downloaded": len(report.tenders),
                "skipped": 0,
                "failed": 0,
                "error": None,
            })
    except Exception as exc:
        db.rollback()
        with _state_lock:
            _pipeline_state.update({
                "state": "failed",
                "error": str(exc),
            })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Páginas principales
# ---------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Dashboard: estado del pipeline + botón para ejecutar."""
    filter_repo = get_filter_repository(db)
    try:
        active_filter = filter_repo.get_active()
    except NoActiveFilterConfigError:
        active_filter = None

    tender_repo = get_tender_repository(db)
    tender_count = tender_repo.count()

    ctx = _pipeline_state_context()
    return _templates.TemplateResponse(
        request,
        "index.html",
        {
            **ctx,
            "filter": active_filter,
            "tender_count": tender_count,
        },
    )


@router.get("/licitacions", response_class=HTMLResponse)
def licitacions_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Llista totes les licitacions puntuades llegides directament de la base de dades (RF-07, J.6)."""
    doc_repo = get_tender_document_repository(db)
    tenders = (
        db.query(TenderModel)
        .order_by(TenderModel.created_at.desc().nulls_last(), TenderModel.data_limit.desc())
        .all()
    )
    documents_by_expedient = {
        t.expedient_id: doc_repo.list_by_expedient(t.expedient_id)
        for t in tenders
    }
    return _templates.TemplateResponse(
        request,
        "tenders.html",
        {
            "tenders": tenders,
            "documents_by_expedient": documents_by_expedient,
        },
    )


@router.get("/filtres", response_class=HTMLResponse)
def filtres_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Formulario de configuración de filtros activos."""
    filter_repo = get_filter_repository(db)
    try:
        active_filter = filter_repo.get_active()
    except NoActiveFilterConfigError:
        active_filter = None

    return _templates.TemplateResponse(
        request,
        "filters.html",
        {"filter": active_filter},
    )


# ---------------------------------------------------------------------------
# Trigger del pipeline (POST desde el dashboard vía HTMX)
# ---------------------------------------------------------------------------

@router.post("/pipeline/trigger", response_class=HTMLResponse)
def trigger_pipeline(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Lanza el pipeline en background y devuelve el partial de estado inmediatamente.

    Si no hay FilterConfig activa, devuelve el partial en estado 'failed'
    con un mensaje de error sin lanzar la tarea.
    """
    filter_repo = get_filter_repository(db)
    try:
        config = filter_repo.get_active()
    except NoActiveFilterConfigError:
        with _state_lock:
            _pipeline_state.update({
                "state": "failed",
                "error": "No hi ha cap configuració de filtres activa. Configura els filtres primer.",
            })
        ctx = _pipeline_state_context()
        return _templates.TemplateResponse(
            request,
            "partials/pipeline_status.html",
            ctx,
        )

    with _state_lock:
        _pipeline_state.update({
            "state": "running",
            "total": 0,
            "downloaded": 0,
            "skipped": 0,
            "failed": 0,
            "error": None,
        })

    background_tasks.add_task(_run_pipeline_task, config)

    ctx = _pipeline_state_context()
    return _templates.TemplateResponse(
        request,
        "partials/pipeline_status.html",
        ctx,
    )


# ---------------------------------------------------------------------------
# Partials (polling HTMX)
# ---------------------------------------------------------------------------

@router.get("/partials/pipeline-status", response_class=HTMLResponse)
def partial_pipeline_status(request: Request) -> HTMLResponse:
    """Fragmento de estado del pipeline — consultado cada 2s por HTMX (RNF-01)."""
    ctx = _pipeline_state_context()
    return _templates.TemplateResponse(
        request,
        "partials/pipeline_status.html",
        ctx,
    )


@router.get("/partials/search-results", response_class=HTMLResponse)
def partial_search_results(request: Request) -> HTMLResponse:
    """Fragmento con los resultados de la última ejecución del pipeline."""
    with _state_lock:
        report = _last_report

    if report is None:
        return HTMLResponse(content="")

    viable = sum(
        1 for t in report.tenders if t.traffic_light in ("green", "yellow"))
    return _templates.TemplateResponse(
        request,
        "partials/search_results.html",
        {
            "report": report,
            "viable_count": viable,
        },
    )
