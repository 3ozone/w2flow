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


class TestGetTenderDocuments:
    """Tests for GET /api/v1/tenders/{id}/documents."""

    def test_returns_200_when_tender_exists(self, client, mock_repository):
        """GET /tenders/{id}/documents must return 200 when tender exists."""
        mock_repository.list_scored = AsyncMock(
            return_value=[_make_scored_tender("uuid-1")]
        )
        mock_repository.list_documents = AsyncMock(return_value=[])
        response = client.get("/api/v1/tenders/uuid-1/documents")
        assert response.status_code == 200

    def test_returns_404_when_tender_not_found(self, client, mock_repository):
        """GET /tenders/{id}/documents must return 404 when tender does not exist."""
        mock_repository.list_scored = AsyncMock(return_value=[])
        response = client.get("/api/v1/tenders/nonexistent-id/documents")
        assert response.status_code == 404

    def test_returns_document_list(self, client, mock_repository):
        """GET /tenders/{id}/documents must return a list of document objects."""
        from app.domain.entities.document import Document
        from app.domain.value_objects.document_type import DocumentType
        mock_repository.list_scored = AsyncMock(
            return_value=[_make_scored_tender("uuid-1")]
        )
        mock_repository.list_documents = AsyncMock(return_value=[
            Document(
                expedient_id="uuid-1",
                doc_id=101,
                titol="Plec de clàusules administratives",
                hash="abc123",
                mida_kb=512.0,
                file_path="downloads/uuid-1/Plec de clàusules administratives",
                type=DocumentType.PCAP,
            )
        ])
        response = client.get("/api/v1/tenders/uuid-1/documents")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["doc_id"] == 101
        assert data[0]["titol"] == "Plec de clàusules administratives"
        assert data[0]["type"] == "pcap"

    def test_returns_empty_list_when_no_documents(self, client, mock_repository):
        """GET /tenders/{id}/documents must return [] when tender has no documents."""
        mock_repository.list_scored = AsyncMock(
            return_value=[_make_scored_tender("uuid-1")]
        )
        mock_repository.list_documents = AsyncMock(return_value=[])
        response = client.get("/api/v1/tenders/uuid-1/documents")
        assert response.json() == []


class TestDownloadTenderDocument:
    """Tests for GET /api/v1/tenders/{id}/documents/{doc_id}/download."""

    def _make_document(self, tmp_path, doc_id: int = 101) -> "Document":
        from app.domain.entities.document import Document
        from app.domain.value_objects.document_type import DocumentType
        pdf_file = tmp_path / "uuid-1" / "plec.pdf"
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        pdf_file.write_bytes(b"%PDF-test")
        return Document(
            expedient_id="uuid-1",
            doc_id=doc_id,
            titol="plec.pdf",
            hash="abc123",
            mida_kb=10.0,
            file_path=str(pdf_file),
            type=DocumentType.PCAP,
        )

    def test_returns_200_with_pdf_content(self, client, mock_repository, tmp_path):
        """GET /tenders/{id}/documents/{doc_id}/download must return the PDF bytes."""
        doc = self._make_document(tmp_path)
        mock_repository.list_scored = AsyncMock(
            return_value=[_make_scored_tender("uuid-1")]
        )
        mock_repository.list_documents = AsyncMock(return_value=[doc])
        response = client.get("/api/v1/tenders/uuid-1/documents/101/download")
        assert response.status_code == 200
        assert response.content == b"%PDF-test"

    def test_returns_pdf_content_type(self, client, mock_repository, tmp_path):
        """GET .../download must return content-type application/pdf."""
        doc = self._make_document(tmp_path)
        mock_repository.list_scored = AsyncMock(
            return_value=[_make_scored_tender("uuid-1")]
        )
        mock_repository.list_documents = AsyncMock(return_value=[doc])
        response = client.get("/api/v1/tenders/uuid-1/documents/101/download")
        assert "application/pdf" in response.headers["content-type"]

    def test_returns_404_when_tender_not_found(self, client, mock_repository):
        """GET .../download must return 404 when the tender does not exist."""
        mock_repository.list_scored = AsyncMock(return_value=[])
        response = client.get("/api/v1/tenders/nonexistent/documents/101/download")
        assert response.status_code == 404

    def test_returns_404_when_document_not_found(self, client, mock_repository):
        """GET .../download must return 404 when the doc_id does not exist."""
        mock_repository.list_scored = AsyncMock(
            return_value=[_make_scored_tender("uuid-1")]
        )
        mock_repository.list_documents = AsyncMock(return_value=[])
        response = client.get("/api/v1/tenders/uuid-1/documents/999/download")
        assert response.status_code == 404


class TestDeleteTender:
    """Tests for DELETE /api/v1/tenders/{id}."""

    def test_returns_204_when_tender_exists(self, client, mock_repository):
        """DELETE /tenders/{id} must return 204 when the tender is deleted."""
        mock_repository.list_scored = AsyncMock(
            return_value=[_make_scored_tender("uuid-1")]
        )
        mock_repository.delete = AsyncMock(return_value=None)
        response = client.delete("/api/v1/tenders/uuid-1")
        assert response.status_code == 204

    def test_calls_repository_delete(self, client, mock_repository):
        """DELETE /tenders/{id} must call repository.delete with the correct id."""
        mock_repository.list_scored = AsyncMock(
            return_value=[_make_scored_tender("uuid-1")]
        )
        mock_repository.delete = AsyncMock(return_value=None)
        client.delete("/api/v1/tenders/uuid-1")
        mock_repository.delete.assert_called_once_with("uuid-1")

    def test_returns_404_when_tender_not_found(self, client, mock_repository):
        """DELETE /tenders/{id} must return 404 when the tender does not exist."""
        mock_repository.list_scored = AsyncMock(return_value=[])
        response = client.delete("/api/v1/tenders/nonexistent-id")
        assert response.status_code == 404

    def test_second_delete_returns_404(self, client, mock_repository):
        """A second DELETE on the same id must return 404."""
        mock_repository.list_scored = AsyncMock(
            side_effect=[
                [_make_scored_tender("uuid-1")],  # primer DELETE — existe
                [],                                # segundo DELETE — ya no existe
            ]
        )
        mock_repository.delete = AsyncMock(return_value=None)
        client.delete("/api/v1/tenders/uuid-1")
        response = client.delete("/api/v1/tenders/uuid-1")
        assert response.status_code == 404
