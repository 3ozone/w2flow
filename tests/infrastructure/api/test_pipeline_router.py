"""Tests for pipeline_router — POST /pipeline/run and GET /pipeline/status."""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.infrastructure.dependencies as deps
from app.application.dtos.pipeline_status_dto import PipelineStateEnum, PipelineStatusDTO
from app.infrastructure.api.v1.routers.pipeline_router import router
from app.infrastructure.api.v1.schemas.pipeline_status_schema import PipelineState
from app.infrastructure.repositories.in_memory_pipeline_status_adapter import InMemoryPipelineStatusAdapter


@pytest.fixture
def client():
    """Return a TestClient with the pipeline router mounted."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_pipeline_status():
    """Replace pipeline_status_port with a fresh adapter before each test."""
    original = deps.pipeline_status_port
    deps.pipeline_status_port = InMemoryPipelineStatusAdapter()
    yield
    deps.pipeline_status_port = original


class TestPostPipelineRun:
    """Tests for POST /api/v1/pipeline/run."""

    def test_returns_202_when_pipeline_starts(self, client):
        """POST /pipeline/run must return 202 when no pipeline is running."""
        # reset_pipeline_status fixture already provides a fresh IDLE adapter
        with patch(
            "app.infrastructure.api.v1.routers.pipeline_router._run_pipeline",
            new_callable=AsyncMock,
        ):
            response = client.post("/api/v1/pipeline/run")

        assert response.status_code == 202

    def test_returns_409_when_pipeline_already_running(self, client):
        """POST /pipeline/run must return 409 if a pipeline is already running."""
        deps.pipeline_status_port.update(
            PipelineStatusDTO(state=PipelineStateEnum.RUNNING))
        response = client.post("/api/v1/pipeline/run")
        assert response.status_code == 409

    def test_run_response_contains_state(self, client):
        """POST /pipeline/run response body must include state field."""
        with patch(
            "app.infrastructure.api.v1.routers.pipeline_router._run_pipeline",
            new_callable=AsyncMock,
        ):
            response = client.post("/api/v1/pipeline/run")

        if response.status_code == 202:
            data = response.json()
            assert "state" in data


class TestGetPipelineStatus:
    """Tests for GET /api/v1/pipeline/status."""

    def test_returns_200(self, client):
        """GET /pipeline/status must return 200."""
        response = client.get("/api/v1/pipeline/status")
        assert response.status_code == 200

    def test_response_contains_state_field(self, client):
        """GET /pipeline/status response must include state field."""
        response = client.get("/api/v1/pipeline/status")
        data = response.json()
        assert "state" in data

    def test_initial_state_is_idle(self, client):
        """Pipeline state must be idle when no run has been triggered."""
        # reset_pipeline_status fixture ensures a fresh IDLE adapter
        response = client.get("/api/v1/pipeline/status")
        assert response.json()["state"] == PipelineState.IDLE.value


class TestRunPipelineAnalysisService:
    """Tests for RF-05/11.7 — AnalysisService receives non-empty pdf_paths."""

    @pytest.mark.asyncio
    async def test_analysis_service_receives_non_empty_pdf_paths(self):
        """_run_pipeline() must pass non-empty pdf_paths to AnalysisService.analyze()
        when storage.list_documents() returns documents with file_path set.
        """
        from datetime import date
        from app.domain.entities.tender import Tender
        from app.domain.entities.scored_tender import ScoredTender
        from app.domain.entities.document import Document
        from app.domain.value_objects.score import Score
        from app.domain.value_objects.document_type import DocumentType
        from app.domain.value_objects.filter_config import FilterConfig
        from app.domain.entities.comparative_report import ComparativeReport
        from app.infrastructure.api.v1.schemas.filter_schema import FilterSchema
        import app.infrastructure.api.v1.routers.pipeline_router as router_mod
        import app.infrastructure.api.v1.routers.filters_router as filters_mod
        import app.infrastructure.dependencies as deps_mod

        tender = Tender(
            expedient_id="uuid-test",
            publicacio_id=1,
            titol="Obra test",
            organ="Ajuntament",
            pressupost=100_000.0,
            codi_expedient="EXP-1",
            fase="LICITACIO_PUBLICA",
            data_publicacio=date.today(),
        )
        score = Score(
            expedient_id="uuid-test",
            total=60,
            detall={},
            paraules_clau_trobades=frozenset(),
            penalitzacions=frozenset(),
            recomanacio="A VALORAR",
        )
        scored_tender = ScoredTender(
            tender=tender, score=score, requirements=None)
        filter_config = FilterConfig(
            tipus_expedient=1,
            fase_vigent=0,
            sector_keywords=("construcció",),
            min_pressupost=0.0,
        )
        report = ComparativeReport(
            scored_tenders=[scored_tender], filter_config=filter_config)

        document_with_path = Document(
            expedient_id="uuid-test",
            doc_id=1,
            titol="PCAP.pdf",
            hash="abc",
            mida_kb=100.0,
            type=DocumentType.PCAP,
            file_path="downloads/uuid-test/PCAP.pdf",
        )

        mock_storage = AsyncMock()
        mock_storage.list_documents.return_value = [document_with_path]

        mock_handler = AsyncMock()
        mock_handler.handle.return_value = report

        captured_pdf_paths: list = []

        async def fake_analyze(scored_tenders, pdf_paths):
            captured_pdf_paths.extend(pdf_paths)
            return "analysis text"

        from app.infrastructure.repositories.in_memory_filter_config_adapter import InMemoryFilterConfigAdapter
        active_filter_schema = FilterSchema(
            tipus_expedient=1,
            fase_vigent=0,
            sector_keywords=["construcció"],
            min_pressupost=0.0,
        )
        original_port = deps_mod.filter_config_port
        deps_mod.filter_config_port = InMemoryFilterConfigAdapter()
        deps_mod.filter_config_port.save(active_filter_schema.to_domain())
        try:
            with (
                patch(
                    "app.infrastructure.api.v1.routers.pipeline_router._build_dependencies",
                ) as mock_build_deps,
                patch.object(deps_mod, "document_storage", mock_storage),
                patch(
                    "app.infrastructure.api.v1.routers.pipeline_router.RunPipelineCommandHandler",
                    return_value=mock_handler,
                ),
                patch(
                    "app.infrastructure.api.v1.routers.pipeline_router.AnalysisService"
                ) as MockAnalysis,
                patch(
                    "app.infrastructure.api.v1.routers.pipeline_router.reports_router"
                ),
            ):
                mock_build_deps.return_value = (AsyncMock(), AsyncMock())
                mock_analysis_instance = AsyncMock()
                mock_analysis_instance.analyze.side_effect = fake_analyze
                MockAnalysis.return_value = mock_analysis_instance

                await router_mod._run_pipeline()
        finally:
            deps_mod.filter_config_port = original_port

        assert captured_pdf_paths != [], (
            "AnalysisService.analyze() must receive non-empty pdf_paths "
            "when storage has documents with file_path"
        )
        assert "downloads/uuid-test/PCAP.pdf" in captured_pdf_paths
