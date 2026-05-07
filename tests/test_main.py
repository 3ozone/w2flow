"""Tests for main.py — FastAPI app wiring and router mounting."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient

import app.infrastructure.dependencies as deps
import app.infrastructure.api.v1.routers.tenders_router as tenders_module
from app.infrastructure.repositories.in_memory_pipeline_status_adapter import InMemoryPipelineStatusAdapter
from app.main import app


@pytest.fixture(autouse=True)
def reset_pipeline():
    """Reset pipeline state between tests."""
    original = deps.pipeline_status_port
    deps.pipeline_status_port = InMemoryPipelineStatusAdapter()
    yield
    deps.pipeline_status_port = original


@pytest.fixture(autouse=True)
def inject_mock_repository():
    """Inject a mock repository so routes don't crash."""
    mock_repo = MagicMock()
    mock_repo.list_scored = AsyncMock(return_value=[])
    original = tenders_module._repository
    tenders_module._repository = mock_repo
    yield mock_repo
    tenders_module._repository = original


@pytest.fixture
def client():
    return TestClient(app)


class TestAppRouting:
    """Verify all routers are mounted at /api/v1."""

    def test_filters_router_is_mounted(self, client):
        """GET /api/v1/filters must not return 404 (router is registered)."""
        response = client.get("/api/v1/filters")
        assert response.status_code != 404

    def test_tenders_router_is_mounted(self, client):
        """GET /api/v1/tenders must not return 404 (router is registered)."""
        response = client.get("/api/v1/tenders")
        assert response.status_code != 404

    def test_reports_router_is_mounted(self, client):
        """GET /api/v1/reports must not return 404 (router is registered)."""
        response = client.get("/api/v1/reports")
        assert response.status_code != 404

    def test_pipeline_status_router_is_mounted(self, client):
        """GET /api/v1/pipeline/status must not return 404 (router is registered)."""
        response = client.get("/api/v1/pipeline/status")
        assert response.status_code != 404

    def test_unknown_route_returns_404(self, client):
        """An unregistered path must return 404."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
