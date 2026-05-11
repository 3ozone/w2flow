"""FastAPI router for comparative reports endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.domain.entities.comparative_report import ComparativeReport
from app.infrastructure.api.v1.schemas.report_schema import ReportSchema

router = APIRouter(tags=["reports"])

# In-memory store: report_id -> ComparativeReport domain entity
# Populated by the pipeline router after each run
_reports: dict[str, ComparativeReport] = {}

# In-memory store: report_id -> narrative analysis text (from AnalysisService)
_reports_analysis: dict[str, str] = {}

# In-memory store: report_id -> creation datetime string
_reports_created_at: dict[str, str] = {}


def add_report(report_id: str, report: ComparativeReport) -> None:
    """Store a ComparativeReport under the given id."""
    _reports[report_id] = report
    _reports_created_at[report_id] = datetime.now().strftime("%d/%m/%Y %H:%M")


def add_analysis(report_id: str, analysis: str) -> None:
    """Store a narrative analysis text under the given report id."""
    _reports_analysis[report_id] = analysis


class _ReportSummary(ReportSchema):
    """ReportSchema extended with its storage id."""

    id: str

    @classmethod
    def from_domain_with_id(cls, report_id: str, report: ComparativeReport) -> "_ReportSummary":
        """Create a _ReportSummary from a ComparativeReport and its id."""
        base = ReportSchema.from_domain(report)
        return cls(
            id=report_id,
            total_count=base.total_count,
            viable_count=base.viable_count,
            tenders=base.tenders,
        )


@router.get("/reports", response_model=list[_ReportSummary])
async def list_reports() -> list[_ReportSummary]:
    """Return a list of all stored report summaries."""
    return [
        _ReportSummary.from_domain_with_id(rid, report)
        for rid, report in _reports.items()
    ]


@router.get("/reports/{report_id}", response_model=ReportSchema)
async def get_report(report_id: str) -> ReportSchema:
    """Return full report detail by id, or 404 if not found."""
    report = _reports.get(report_id)
    if report is None:
        raise HTTPException(
            status_code=404, detail=f"Report '{report_id}' not found")
    return ReportSchema.from_domain(report)


class _AnalysisResponse(BaseModel):
    analysis: str


@router.get("/reports/{report_id}/analysis", response_model=_AnalysisResponse)
async def get_report_analysis(report_id: str) -> _AnalysisResponse:
    """Return the narrative analysis text for a report, or 404 if not found."""
    text = _reports_analysis.get(report_id)
    if text is None:
        raise HTTPException(
            status_code=404, detail=f"Analysis for report '{report_id}' not found")
    return _AnalysisResponse(analysis=text)


@router.delete("/reports/{report_id}", status_code=204)
async def delete_report(report_id: str) -> Response:
    """Delete a report and its analysis from the in-memory store, or 404 if not found."""
    if report_id not in _reports:
        raise HTTPException(
            status_code=404, detail=f"Report '{report_id}' not found")
    del _reports[report_id]
    _reports_analysis.pop(report_id, None)
    _reports_created_at.pop(report_id, None)
    return Response(status_code=204)
