"""FastAPI router for HTML UI pages (no /api/v1 prefix)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.infrastructure.api.v1.routers import reports_router as reports_module
from app.infrastructure import dependencies
from app.infrastructure.api.v1.schemas.filter_schema import FilterSchema

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
    status = dependencies.pipeline_status_port.get()
    repo = dependencies.repository
    tender_count = len(await repo.list_scored(page=0, size=10_000)) if repo else 0
    report_count = len(reports_module._reports)
    fc = dependencies.filter_config_port.get()
    active_filter = FilterSchema.from_domain(fc) if fc is not None else None
    return _templates.TemplateResponse(
        request,
        "index.html",
        {
            "filter": active_filter,
            "state": status.state.value,
            "total": status.total,
            "downloaded": status.downloaded,
            "skipped": status.skipped,
            "failed": status.failed,
            "error": status.error,
            "tender_count": tender_count,
            "report_count": report_count,
        },
    )


# ---------------------------------------------------------------------------
# Partials
# ---------------------------------------------------------------------------

@router.get("/partials/pipeline-status", response_class=HTMLResponse)
async def partial_pipeline_status(request: Request) -> HTMLResponse:
    """Return the pipeline status partial fragment (polled by HTMX)."""
    status = dependencies.pipeline_status_port.get()
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


@router.get("/partials/search-results", response_class=HTMLResponse)
async def partial_search_results(request: Request) -> HTMLResponse:
    """Return the latest report as inline search results partial."""
    if not reports_module._reports:
        return HTMLResponse(content="")
    report_id = list(reports_module._reports.keys())[-1]
    report = reports_module._reports[report_id]
    analysis = reports_module._reports_analysis.get(report_id, "")
    viable_count = len(report.get_viable_tenders())
    return _templates.TemplateResponse(
        request,
        "partials/search_results.html",
        {
            "report_id": report_id,
            "report": report,
            "analysis": analysis,
            "viable_count": viable_count,
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

@router.get("/tenders", response_class=RedirectResponse)
async def tenders_page() -> RedirectResponse:
    """Deprecated — redirects to / (search page)."""
    return RedirectResponse(url="/", status_code=301)


@router.get("/licitaciones", response_class=HTMLResponse)
async def licitaciones_page(request: Request) -> HTMLResponse:
    """Licitacions page — full list of scored tenders from the DB."""
    repo = dependencies.repository
    scored = await repo.list_scored(page=0, size=10_000) if repo else []
    from app.infrastructure.api.v1.schemas.tender_schema import TenderSchema
    tenders = [TenderSchema.from_domain(st) for st in scored]
    return _templates.TemplateResponse(
        request,
        "tenders.html",
        {"tenders": tenders},
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
        {
            "reports": list(reports_module._reports.items()),
            "reports_created_at": reports_module._reports_created_at,
        },
    )


@router.get("/reports/{report_id}", response_class=HTMLResponse)
async def report_detail_page(request: Request, report_id: str) -> HTMLResponse:
    """Report detail page with tenders table and optional Gemini analysis."""
    from fastapi import HTTPException as _HTTPException
    report = reports_module._reports.get(report_id)
    if report is None:
        raise _HTTPException(
            status_code=404, detail=f"Report '{report_id}' not found")
    analysis = reports_module._reports_analysis.get(report_id)
    viable_count = len(report.get_viable_tenders())
    created_at = reports_module._reports_created_at.get(report_id, "")
    return _templates.TemplateResponse(
        request,
        "report_detail.html",
        {
            "report_id": report_id,
            "report": report,
            "analysis": analysis,
            "viable_count": viable_count,
            "created_at": created_at,
        },
    )


# ---------------------------------------------------------------------------
# Filters page
# ---------------------------------------------------------------------------

@router.get("/filters", response_class=HTMLResponse)
async def filters_page(request: Request) -> HTMLResponse:
    """Filter configuration form page."""
    fc = dependencies.filter_config_port.get()
    active_filter = FilterSchema.from_domain(fc) if fc is not None else None
    return _templates.TemplateResponse(
        request,
        "filters.html",
        {"filter": active_filter},
    )
