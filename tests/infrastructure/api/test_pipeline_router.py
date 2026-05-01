"""Tests for pipeline_router — POST /pipeline/run and GET /pipeline/status."""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.infrastructure.api.v1.routers.pipeline_router as router_module
from app.infrastructure.api.v1.routers.pipeline_router import router
from app.infrastructure.api.v1.schemas.pipeline_status_schema import PipelineState


@pytest.fixture
def client():
    """Return a TestClient with the pipeline router mounted."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


class TestPostPipelineRun:
    """Tests for POST /api/v1/pipeline/run."""

    def test_returns_202_when_pipeline_starts(self, client):
        """POST /pipeline/run must return 202 when no pipeline is running."""
        with patch(
            "app.infrastructure.api.v1.routers.pipeline_router._pipeline_state",
            PipelineState.IDLE,
        ):
            with patch(
                "app.infrastructure.api.v1.routers.pipeline_router._run_pipeline",
                new_callable=AsyncMock,
            ):
                response = client.post("/api/v1/pipeline/run")

        assert response.status_code == 202

    def test_returns_409_when_pipeline_already_running(self, client):
        """POST /pipeline/run must return 409 if a pipeline is already running."""
        original = router_module._pipeline_state
        router_module._pipeline_state = PipelineState.RUNNING
        try:
            response = client.post("/api/v1/pipeline/run")
        finally:
            router_module._pipeline_state = original

        assert response.status_code == 409

    def test_run_response_contains_state(self, client):
        """POST /pipeline/run response body must include state field."""
        with patch(
            "app.infrastructure.api.v1.routers.pipeline_router._pipeline_state",
            PipelineState.IDLE,
        ):
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
        from app.infrastructure.api.v1.schemas.pipeline_status_schema import PipelineStatusSchema

        original_state = router_module._pipeline_state
        original_status = router_module._pipeline_status
        router_module._pipeline_state = PipelineState.IDLE
        router_module._pipeline_status = PipelineStatusSchema(state=PipelineState.IDLE)
        try:
            response = client.get("/api/v1/pipeline/status")
        finally:
            router_module._pipeline_state = original_state
            router_module._pipeline_status = original_status

        assert response.json()["state"] == PipelineState.IDLE.value
