"""Tests for tenders_router — GET /tenders and GET /tenders/{id}."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.infrastructure.api.v1.routers.tenders_router as router_module
from app.infrastructure.api.v1.routers.tenders_router import router
from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.value_objects.score import Score
from app.domain.value_objects.requirements import Requirements


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


@pytest.fixture
def mock_repository():
    return MagicMock()


@pytest.fixture
def client(mock_repository):
    """Return a TestClient with tenders router and injected mock repository."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    router_module._repository = mock_repository
    return TestClient(app)


class TestGetTenders:
    """Tests for GET /api/v1/tenders."""

    def test_returns_200(self, client, mock_repository):
        """GET /tenders must return 200."""
        mock_repository.list_scored = AsyncMock(return_value=[])
        response = client.get("/api/v1/tenders")
        assert response.status_code == 200

    def test_returns_list(self, client, mock_repository):
        """GET /tenders must return a JSON array."""
        mock_repository.list_scored = AsyncMock(return_value=[])
        response = client.get("/api/v1/tenders")
        assert isinstance(response.json(), list)

    def test_returns_scored_tenders(self, client, mock_repository):
        """GET /tenders must return serialized scored tenders."""
        mock_repository.list_scored = AsyncMock(
            return_value=[_make_scored_tender("uuid-1")]
        )
        response = client.get("/api/v1/tenders")
        data = response.json()
        assert len(data) == 1
        assert data[0]["expedient_id"] == "uuid-1"
        assert "score" in data[0]

    def test_accepts_page_and_size_query_params(self, client, mock_repository):
        """GET /tenders must accept page and size query parameters."""
        mock_repository.list_scored = AsyncMock(return_value=[])
        response = client.get("/api/v1/tenders?page=1&size=10")
        assert response.status_code == 200
        mock_repository.list_scored.assert_called_once_with(page=1, size=10)


class TestGetTenderById:
    """Tests for GET /api/v1/tenders/{id}."""

    def test_returns_200_when_found(self, client, mock_repository):
        """GET /tenders/{id} must return 200 when the tender exists."""
        mock_repository.list_scored = AsyncMock(
            return_value=[_make_scored_tender("uuid-1")]
        )
        response = client.get("/api/v1/tenders/uuid-1")
        assert response.status_code == 200

    def test_returns_tender_detail(self, client, mock_repository):
        """GET /tenders/{id} must return the tender with score details."""
        mock_repository.list_scored = AsyncMock(
            return_value=[_make_scored_tender("uuid-1")]
        )
        response = client.get("/api/v1/tenders/uuid-1")
        data = response.json()
        assert data["expedient_id"] == "uuid-1"
        assert data["score"]["total"] == 55

    def test_returns_404_when_not_found(self, client, mock_repository):
        """GET /tenders/{id} must return 404 when tender does not exist."""
        mock_repository.list_scored = AsyncMock(return_value=[])
        response = client.get("/api/v1/tenders/nonexistent-id")
        assert response.status_code == 404
