"""Tests for filters_router — GET /filters and PUT /filters."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.infrastructure.api.v1.routers.filters_router as router_module
from app.infrastructure.api.v1.routers.filters_router import router
from app.infrastructure.api.v1.schemas.filter_schema import FilterSchema


@pytest.fixture
def client():
    """Return a TestClient with the filters router mounted."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_filter_config():
    """Restore the active filter config to None after each test."""
    original = router_module._active_filter
    yield
    router_module._active_filter = original


_VALID_PAYLOAD = {
    "tipus_expedient": 1,
    "fase_vigent": 0,
    "max_results": 20,
    "sector_keywords": ["construcció"],
    "min_pressupost": 100_000.0,
}


class TestGetFilters:
    """Tests for GET /api/v1/filters."""

    def test_returns_200(self, client):
        """GET /filters must return 200."""
        response = client.get("/api/v1/filters")
        assert response.status_code == 200

    def test_returns_null_when_no_filter_configured(self, client):
        """GET /filters must return null when no filter has been set."""
        router_module._active_filter = None
        response = client.get("/api/v1/filters")
        assert response.json() is None

    def test_returns_active_filter_when_configured(self, client):
        """GET /filters must return the active FilterSchema when set."""
        router_module._active_filter = FilterSchema(**_VALID_PAYLOAD)
        response = client.get("/api/v1/filters")
        data = response.json()
        assert data["tipus_expedient"] == 1
        assert data["fase_vigent"] == 0


class TestPutFilters:
    """Tests for PUT /api/v1/filters."""

    def test_valid_payload_returns_200(self, client):
        """PUT /filters with valid data must return 200."""
        response = client.put("/api/v1/filters", json=_VALID_PAYLOAD)
        assert response.status_code == 200

    def test_updated_filter_is_returned_in_response(self, client):
        """PUT /filters must echo back the updated filter config."""
        response = client.put("/api/v1/filters", json=_VALID_PAYLOAD)
        data = response.json()
        assert data["tipus_expedient"] == 1
        assert data["sector_keywords"] == ["construcció"]

    def test_invalid_payload_returns_422(self, client):
        """PUT /filters with invalid data must return 422."""
        response = client.put(
            "/api/v1/filters", json={"tipus_expedient": -1, "fase_vigent": 0})
        assert response.status_code == 422

    def test_updated_filter_persists_for_get(self, client):
        """After PUT /filters, GET /filters must return the new config."""
        client.put("/api/v1/filters", json=_VALID_PAYLOAD)
        response = client.get("/api/v1/filters")
        assert response.json()["min_pressupost"] == 100_000.0
