"""Tests for ui_router — HTML page endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.infrastructure.api.v1.routers.ui_router import router


@pytest.fixture
def client():
    """Return a TestClient with the ui router mounted."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, follow_redirects=False)


class TestTendersPageDeprecated:
    """Tests for Fase 15.5 — GET /tenders must redirect to /."""

    def test_get_tenders_redirects_to_root(self, client):
        """GET /tenders must return 301 redirect to /."""
        response = client.get("/tenders")
        assert response.status_code in (301, 302, 308)

    def test_get_tenders_redirect_location_is_root(self, client):
        """GET /tenders redirect must point to /."""
        response = client.get("/tenders")
        assert response.headers["location"] in ("/", "http://testserver/")


class TestLicitacionesPage:
    """Tests for GET /licitaciones — full tenders listing page."""

    def test_get_licitaciones_returns_200(self, client):
        """GET /licitaciones must return 200 OK."""
        response = client.get("/licitaciones")
        assert response.status_code == 200

    def test_get_licitaciones_renders_html(self, client):
        """GET /licitaciones must return HTML content."""
        response = client.get("/licitaciones")
        assert "text/html" in response.headers["content-type"]

    def test_get_licitaciones_not_a_redirect(self, client):
        """GET /licitaciones must not redirect (it is its own page)."""
        response = client.get("/licitaciones")
        assert response.status_code not in (301, 302, 307, 308)
