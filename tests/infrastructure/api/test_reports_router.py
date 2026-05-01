"""Tests for reports_router — GET /reports and GET /reports/{id}."""

from datetime import date
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.infrastructure.api.v1.routers.reports_router as router_module
from app.infrastructure.api.v1.routers.reports_router import router
from app.domain.entities.comparative_report import ComparativeReport
from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.value_objects.filter_config import FilterConfig
from app.domain.value_objects.requirements import Requirements
from app.domain.value_objects.score import Score


def _make_filter_config() -> FilterConfig:
    return FilterConfig(tipus_expedient=1, fase_vigent=0, sector_keywords=("obra",))


def _make_scored_tender(expedient_id: str = "uuid-1") -> ScoredTender:
    tender = Tender(
        expedient_id=expedient_id,
        publicacio_id=42,
        titol="Obres de pavimentació",
        organ="Ajuntament de Girona",
        pressupost=300_000.0,
        codi_expedient="EXP-001",
        fase="0",
        data_publicacio=date(2026, 5, 1),
    )
    score = Score(
        expedient_id=expedient_id,
        total=55,
        detall={"pressupost": 20, "sector_positiu": 25, "sector_negatiu": 0,
                "procediment_obert": 10, "subcontractació": 0},
        paraules_clau_trobades=("obra civil",),
        penalitzacions=(),
        recomanacio="✅ RECOMANADA",
    )
    requirements = Requirements(
        expedient_id=expedient_id,
        solvency_requirements=(),
        technical_requirements=(),
        adjudication_criteria=(),
        special_clauses=(),
        raw_agent_output="",
    )
    return ScoredTender(tender=tender, score=score, requirements=requirements)


def _make_report(report_id: str = "report-1") -> ComparativeReport:
    return ComparativeReport(
        scored_tenders=[_make_scored_tender()],
        filter_config=_make_filter_config(),
    )


@pytest.fixture(autouse=True)
def reset_reports():
    """Clear in-memory reports store before each test."""
    original = dict(router_module._reports)
    router_module._reports.clear()
    yield
    router_module._reports.clear()
    router_module._reports.update(original)


@pytest.fixture
def client():
    """Return a TestClient with the reports router mounted."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


class TestGetReports:
    """Tests for GET /api/v1/reports."""

    def test_returns_200(self, client):
        """GET /reports must return 200."""
        response = client.get("/api/v1/reports")
        assert response.status_code == 200

    def test_returns_empty_list_when_no_reports(self, client):
        """GET /reports must return [] when no reports exist."""
        response = client.get("/api/v1/reports")
        assert response.json() == []

    def test_returns_list_of_report_summaries(self, client):
        """GET /reports must return a list with report summaries."""
        router_module._reports["report-1"] = _make_report()
        response = client.get("/api/v1/reports")
        data = response.json()
        assert len(data) == 1
        assert "id" in data[0]
        assert "total_count" in data[0]

    def test_summary_contains_correct_counts(self, client):
        """GET /reports summary must contain accurate tender counts."""
        router_module._reports["report-1"] = _make_report()
        response = client.get("/api/v1/reports")
        summary = response.json()[0]
        assert summary["total_count"] == 1


class TestGetReportById:
    """Tests for GET /api/v1/reports/{id}."""

    def test_returns_200_when_found(self, client):
        """GET /reports/{id} must return 200 when report exists."""
        router_module._reports["report-1"] = _make_report()
        response = client.get("/api/v1/reports/report-1")
        assert response.status_code == 200

    def test_returns_full_report_detail(self, client):
        """GET /reports/{id} must return full report with tenders."""
        router_module._reports["report-1"] = _make_report()
        response = client.get("/api/v1/reports/report-1")
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["tenders"]) == 1
        assert data["tenders"][0]["expedient_id"] == "uuid-1"

    def test_returns_404_when_not_found(self, client):
        """GET /reports/{id} must return 404 for unknown id."""
        response = client.get("/api/v1/reports/nonexistent")
        assert response.status_code == 404


class TestGetReportAnalysis:
    """Tests for GET /api/v1/reports/{id}/analysis."""

    @pytest.fixture(autouse=True)
    def reset_analysis(self):
        """Clear in-memory analysis store before each test."""
        original = dict(router_module._reports_analysis)
        router_module._reports_analysis.clear()
        yield
        router_module._reports_analysis.clear()
        router_module._reports_analysis.update(original)

    def test_returns_200_with_analysis_text(self, client):
        """GET /reports/{id}/analysis returns 200 and the analysis text."""
        router_module._reports_analysis["report-1"] = "Anàlisi comparativa."
        response = client.get("/api/v1/reports/report-1/analysis")
        assert response.status_code == 200
        assert response.json()["analysis"] == "Anàlisi comparativa."

    def test_returns_404_when_not_found(self, client):
        """GET /reports/{id}/analysis returns 404 for unknown id."""
        response = client.get("/api/v1/reports/nonexistent/analysis")
        assert response.status_code == 404

    def test_response_contains_only_analysis_key(self, client):
        """Response body must have exactly the 'analysis' key."""
        router_module._reports_analysis["report-1"] = "Informe."
        response = client.get("/api/v1/reports/report-1/analysis")
        data = response.json()
        assert set(data.keys()) == {"analysis"}


class TestDeleteReport:
    """Tests for DELETE /api/v1/reports/{id}."""

    @pytest.fixture(autouse=True)
    def reset_analysis(self):
        """Clear in-memory analysis store before each test."""
        original = dict(router_module._reports_analysis)
        router_module._reports_analysis.clear()
        yield
        router_module._reports_analysis.clear()
        router_module._reports_analysis.update(original)

    def test_returns_204_when_report_exists(self, client):
        """DELETE /reports/{id} must return 204 when the report exists."""
        router_module._reports["report-1"] = _make_report()
        response = client.delete("/api/v1/reports/report-1")
        assert response.status_code == 204

    def test_removes_report_from_store(self, client):
        """DELETE /reports/{id} must remove the entry from _reports."""
        router_module._reports["report-1"] = _make_report()
        client.delete("/api/v1/reports/report-1")
        assert "report-1" not in router_module._reports

    def test_removes_analysis_from_store(self, client):
        """DELETE /reports/{id} must also remove the analysis if it exists."""
        router_module._reports["report-1"] = _make_report()
        router_module._reports_analysis["report-1"] = "Anàlisi."
        client.delete("/api/v1/reports/report-1")
        assert "report-1" not in router_module._reports_analysis

    def test_returns_404_when_report_not_found(self, client):
        """DELETE /reports/{id} must return 404 for unknown id."""
        response = client.delete("/api/v1/reports/nonexistent")
        assert response.status_code == 404

    def test_second_delete_returns_404(self, client):
        """A second DELETE on the same id must return 404."""
        router_module._reports["report-1"] = _make_report()
        client.delete("/api/v1/reports/report-1")
        response = client.delete("/api/v1/reports/report-1")
        assert response.status_code == 404
