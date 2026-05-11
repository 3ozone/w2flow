"""Tests for health_router — GET /health."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.infrastructure.api.v1.routers.health_router import router


@pytest.fixture
def client():
    """Return a TestClient with the health router mounted."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


class TestGetHealth:
    """Tests for GET /api/v1/health."""

    def test_returns_200(self, client):
        """GET /health must always return 200."""
        with patch(
            "app.infrastructure.api.v1.routers.health_router._check_db",
            return_value="ok",
        ):
            response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_returns_ok_when_db_healthy(self, client):
        """GET /health returns status=ok and db=ok when DB responds."""
        with patch(
            "app.infrastructure.api.v1.routers.health_router._check_db",
            return_value="ok",
        ):
            response = client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["db"] == "ok"

    def test_returns_degraded_when_db_fails(self, client):
        """GET /health returns status=degraded and db=error when DB is unreachable."""
        with patch(
            "app.infrastructure.api.v1.routers.health_router._check_db",
            return_value="error",
        ):
            response = client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "degraded"
        assert data["db"] == "error"

    def test_still_returns_200_when_db_fails(self, client):
        """GET /health must return 200 even when DB is degraded."""
        with patch(
            "app.infrastructure.api.v1.routers.health_router._check_db",
            return_value="error",
        ):
            response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_response_contains_required_keys(self, client):
        """GET /health response body must contain exactly 'status' and 'db' keys."""
        with patch(
            "app.infrastructure.api.v1.routers.health_router._check_db",
            return_value="ok",
        ):
            response = client.get("/api/v1/health")
        assert set(response.json().keys()) == {"status", "db"}
