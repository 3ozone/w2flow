"""FastAPI router for HTML UI pages (no /api/v1 prefix)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.infrastructure.api.v1.routers import filters_router as filters_module
from app.infrastructure.api.v1.routers import pipeline_router as pipeline_module
from app.infrastructure.api.v1.routers import reports_router as reports_module
from app.infrastructure import dependencies

router = APIRouter(tags=["ui"])

_templates = Jinja2Templates(
    directory=Path(__file__).resolve().parents[4] / "templates"
)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Dashboard: pipeline trigger + status."""
    status = pipeline_module._pipeline_status
    return _templates.TemplateResponse(
        request,
        "index.html",
        {
            "filter": filters_module._active_filter,
            "state": status.state.value,
            "total": status.total,
            "downloaded": status.downloaded,
            "skipped": status.skipped,
            "failed": status.failed,
            "error": status.error,
        },
    )


# ---------------------------------------------------------------------------
# Partials
# ---------------------------------------------------------------------------

@router.get("/partials/pipeline-status", response_class=HTMLResponse)
async def partial_pipeline_status(request: Request) -> HTMLResponse:
    """Return the pipeline status partial fragment (polled by HTMX)."""
    status = pipeline_module._pipeline_status
    return _templates.TemplateResponse(
        request,
        "partials/pipeline_status.html",
        {
            "state": status.state.value,
            "total": status.total,
            "downloaded": status.downloaded,
            "skipped": status.skipped,
            "failed": status.failed,
            "error": status.error,
        },
    )


@router.get("/partials/health", response_class=HTMLResponse)
async def partial_health(request: Request) -> HTMLResponse:
    """Return a small health badge fragment."""
    from app.infrastructure.api.v1.routers.health_router import _check_db
    db = _check_db()
    if db == "ok":
        html = '<span id="health-badge" hx-get="/partials/health" hx-trigger="every 30s" hx-swap="outerHTML" class="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">● DB ok</span>'
    else:
        html = '<span id="health-badge" hx-get="/partials/health" hx-trigger="every 30s" hx-swap="outerHTML" class="inline-flex items-center gap-1 rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-700">● DB error</span>'
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# Tenders page
# ---------------------------------------------------------------------------

@router.get("/tenders", response_class=HTMLResponse)
async def tenders_page(request: Request) -> HTMLResponse:
    """Tenders table page."""
    repo = dependencies.repository
    scored = await repo.list_scored(page=0, size=10_000) if repo else []
    return _templates.TemplateResponse(
        request,
        "tenders.html",
        {"tenders": scored},
    )


@router.get("/partials/tenders/{expedient_id}/documents", response_class=HTMLResponse)
async def partial_tender_documents(request: Request, expedient_id: str) -> HTMLResponse:
    """Return the documents partial for a given tender (loaded on expand)."""
    repo = dependencies.repository
    docs = await repo.list_documents(expedient_id) if repo else []
    return _templates.TemplateResponse(
        request,
        "partials/tender_documents.html",
        {"expedient_id": expedient_id, "documents": docs},
    )


# ---------------------------------------------------------------------------
# Reports pages
# ---------------------------------------------------------------------------

@router.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request) -> HTMLResponse:
    """Reports list page."""
    return _templates.TemplateResponse(
        request,
        "reports.html",
        {"reports": list(reports_module._reports.items())},
    )


@router.get("/reports/{report_id}", response_class=HTMLResponse)
async def report_detail_page(request: Request, report_id: str) -> HTMLResponse:
    """Report detail page with tenders table and optional Gemini analysis."""
    from fastapi import HTTPException as _HTTPException
    report = reports_module._reports.get(report_id)
    if report is None:
        raise _HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    analysis = reports_module._reports_analysis.get(report_id)
    viable_count = len(report.get_viable_tenders())
    return _templates.TemplateResponse(
        request,
        "report_detail.html",
        {
            "report_id": report_id,
            "report": report,
            "analysis": analysis,
            "viable_count": viable_count,
        },
    )


# ---------------------------------------------------------------------------
# Filters page
# ---------------------------------------------------------------------------

@router.get("/filters", response_class=HTMLResponse)
async def filters_page(request: Request) -> HTMLResponse:
    """Filter configuration form page."""
    return _templates.TemplateResponse(
        request,
        "filters.html",
        {"filter": filters_module._active_filter},
    )
