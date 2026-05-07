"""Tests for the real pipeline wiring in pipeline_router._run_pipeline."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

import app.infrastructure.api.v1.routers.pipeline_router as pipeline_module
import app.infrastructure.api.v1.routers.filters_router as filters_module
from app.infrastructure.api.v1.routers.pipeline_router import router
from app.infrastructure.api.v1.schemas.filter_schema import FilterSchema
from app.infrastructure.api.v1.schemas.pipeline_status_schema import PipelineState
from app.domain.entities.tender import Tender
from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.comparative_report import ComparativeReport
from app.domain.value_objects.score import Score
from app.domain.value_objects.filter_config import FilterConfig
from app.domain.value_objects.requirements import Requirements


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_tender(expedient_id: str = "uuid-1") -> Tender:
    return Tender(
        expedient_id=expedient_id,
        publicacio_id=42,
        titol="Obres de pavimentació",
        organ="Ajuntament de Girona",
        pressupost=500_000.0,
        codi_expedient="EXP-001",
        fase="0",
        data_publicacio=date(2026, 5, 1),
    )


def _make_scored_tender(expedient_id: str = "uuid-1") -> ScoredTender:
    tender = _make_tender(expedient_id)
    score = Score(
        expedient_id=expedient_id,
        total=55,
        detall={},
        paraules_clau_trobades=(),
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


@pytest.fixture(autouse=True)
def reset_state():
    """Reset pipeline and filter state before each test."""
    import app.infrastructure.dependencies as deps
    from app.infrastructure.repositories.in_memory_filter_config_adapter import InMemoryFilterConfigAdapter
    from app.infrastructure.repositories.in_memory_pipeline_status_adapter import InMemoryPipelineStatusAdapter
    original_filter_port = deps.filter_config_port
    original_status_port = deps.pipeline_status_port
    deps.filter_config_port = InMemoryFilterConfigAdapter()
    deps.pipeline_status_port = InMemoryPipelineStatusAdapter()
    yield
    deps.filter_config_port = original_filter_port
    deps.pipeline_status_port = original_status_port


@pytest.fixture
def active_filter():
    """Set an active filter via filter_config_port."""
    import app.infrastructure.dependencies as deps
    from app.domain.value_objects.filter_config import FilterConfig
    fc = FilterConfig(
        tipus_expedient=1,
        fase_vigent=0,
        max_results=20,
        sector_keywords=("obres",),
        min_pressupost=0.0,
    )
    deps.filter_config_port.save(fc)
    return fc


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPipelineWiring:
    """Verify that _run_pipeline delegates to RunPipelineCommandHandler and persists results."""

    def _make_report(self) -> ComparativeReport:
        filter_config = FilterConfig(
            tipus_expedient=1,
            fase_vigent=0,
            sector_keywords=("obres",),
            min_pressupost=0.0,
        )
        return ComparativeReport(
            scored_tenders=[_make_scored_tender()],
            filter_config=filter_config,
        )

    @pytest.mark.asyncio
    async def test_pipeline_calls_run_pipeline_handler(self, active_filter):
        """_run_pipeline must call RunPipelineCommandHandler.handle()."""
        with (
            patch("app.infrastructure.api.v1.routers.pipeline_router.RunPipelineCommandHandler") as MockHandler,
            patch("app.infrastructure.api.v1.routers.pipeline_router._build_dependencies") as mock_deps,
        ):
            mock_deps.return_value = (MagicMock(), MagicMock())
            mock_instance = MagicMock()
            mock_instance.handle = AsyncMock(return_value=self._make_report())
            MockHandler.return_value = mock_instance

            await pipeline_module._run_pipeline()

            mock_instance.handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_pipeline_sets_completed_state_on_success(self, active_filter):
        """_run_pipeline must set state to COMPLETED after successful run."""
        import app.infrastructure.dependencies as deps
        from app.application.dtos.pipeline_status_dto import PipelineStateEnum
        with (
            patch("app.infrastructure.api.v1.routers.pipeline_router.RunPipelineCommandHandler") as MockHandler,
            patch("app.infrastructure.api.v1.routers.pipeline_router._build_dependencies") as mock_deps,
        ):
            mock_deps.return_value = (MagicMock(), MagicMock())
            MockHandler.return_value.handle = AsyncMock(
                return_value=self._make_report())

            await pipeline_module._run_pipeline()

            assert deps.pipeline_status_port.get().state == PipelineStateEnum.COMPLETED

    @pytest.mark.asyncio
    async def test_pipeline_sets_failed_state_on_error(self, active_filter):
        """_run_pipeline must set state to FAILED if an exception is raised."""
        import app.infrastructure.dependencies as deps
        from app.application.dtos.pipeline_status_dto import PipelineStateEnum
        with (
            patch("app.infrastructure.api.v1.routers.pipeline_router._build_dependencies") as mock_deps,
        ):
            mock_deps.side_effect = RuntimeError("DB unavailable")

            await pipeline_module._run_pipeline()

            assert deps.pipeline_status_port.get().state == PipelineStateEnum.FAILED
            assert "DB unavailable" in deps.pipeline_status_port.get().error

    @pytest.mark.asyncio
    async def test_pipeline_without_active_filter_sets_failed(self):
        """_run_pipeline must set FAILED state if no filter is configured."""
        import app.infrastructure.dependencies as deps
        from app.application.dtos.pipeline_status_dto import PipelineStateEnum
        # reset_state fixture already sets an empty adapter (no filter saved)

        await pipeline_module._run_pipeline()

        assert deps.pipeline_status_port.get().state == PipelineStateEnum.FAILED
        assert deps.pipeline_status_port.get().error is not None

    @pytest.mark.asyncio
    async def test_pipeline_stores_report_in_reports_router(self, active_filter):
        """After _run_pipeline completes, reports_router._reports must contain one entry."""
        import app.infrastructure.api.v1.routers.reports_router as reports_module

        original_reports = reports_module._reports.copy()
        reports_module._reports.clear()

        try:
            with (
                patch("app.infrastructure.api.v1.routers.pipeline_router.RunPipelineCommandHandler") as MockHandler,
                patch("app.infrastructure.api.v1.routers.pipeline_router._build_dependencies") as mock_deps,
            ):
                mock_deps.return_value = (MagicMock(), MagicMock())
                MockHandler.return_value.handle = AsyncMock(
                    return_value=self._make_report())

                await pipeline_module._run_pipeline()

            assert len(reports_module._reports) == 1
            report = next(iter(reports_module._reports.values()))
            assert len(report.scored_tenders) == 1
            assert report.scored_tenders[0].tender.expedient_id == "uuid-1"
        finally:
            reports_module._reports.clear()
            reports_module._reports.update(original_reports)

    @pytest.mark.asyncio
    async def test_get_reports_returns_report_after_pipeline(self, active_filter):
        """GET /reports must return the stored report after the pipeline runs."""
        import app.infrastructure.api.v1.routers.reports_router as reports_module
        from app.infrastructure.api.v1.routers.reports_router import router as reports_rtr

        original_reports = reports_module._reports.copy()
        reports_module._reports.clear()

        try:
            with (
                patch("app.infrastructure.api.v1.routers.pipeline_router.RunPipelineCommandHandler") as MockHandler,
                patch("app.infrastructure.api.v1.routers.pipeline_router._build_dependencies") as mock_deps,
            ):
                mock_deps.return_value = (MagicMock(), MagicMock())
                MockHandler.return_value.handle = AsyncMock(
                    return_value=self._make_report())

                await pipeline_module._run_pipeline()

            app_with_reports = FastAPI()
            app_with_reports.include_router(reports_rtr, prefix="/api/v1")
            tc = TestClient(app_with_reports)
            response = tc.get("/api/v1/reports")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["total_count"] == 1
        finally:
            reports_module._reports.clear()
            reports_module._reports.update(original_reports)

    @pytest.mark.asyncio
    async def test_pipeline_stores_analysis_in_reports_router(self, active_filter):
        """After _run_pipeline completes, reports_router._reports_analysis must contain the agent text."""
        import app.infrastructure.api.v1.routers.reports_router as reports_module

        original_reports = reports_module._reports.copy()
        original_analysis = getattr(
            reports_module, "_reports_analysis", {}).copy()
        reports_module._reports.clear()
        if hasattr(reports_module, "_reports_analysis"):
            reports_module._reports_analysis.clear()

        try:
            with (
                patch("app.infrastructure.api.v1.routers.pipeline_router.RunPipelineCommandHandler") as MockHandler,
                patch("app.infrastructure.api.v1.routers.pipeline_router.AnalysisService") as MockAnalysis,
                patch("app.infrastructure.api.v1.routers.pipeline_router._build_dependencies") as mock_deps,
            ):
                mock_deps.return_value = (MagicMock(), MagicMock())
                MockHandler.return_value.handle = AsyncMock(
                    return_value=self._make_report())
                MockAnalysis.return_value.analyze = AsyncMock(
                    return_value="Anàlisi comparativa de licitacions.")

                await pipeline_module._run_pipeline()

            assert hasattr(reports_module, "_reports_analysis"), (
                "reports_router must have a _reports_analysis dict"
            )
            assert len(reports_module._reports_analysis) == 1
            analysis_text = next(
                iter(reports_module._reports_analysis.values()))
            assert "Anàlisi" in analysis_text
        finally:
            reports_module._reports.clear()
            reports_module._reports.update(original_reports)
            if hasattr(reports_module, "_reports_analysis"):
                reports_module._reports_analysis.clear()
                reports_module._reports_analysis.update(original_analysis)
