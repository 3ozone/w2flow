"""Tests for ContractacioPublicaClient using mocked HTTP responses."""

from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest

from app.domain.value_objects.filter_config import FilterConfig
from app.domain.exceptions.download_error import DownloadError
from app.infrastructure.services.contractacio_publica_client import (
    ContractacioPublicaClient,
)


def _make_filter_config() -> FilterConfig:
    return FilterConfig(
        tipus_expedient=1,
        fase_vigent=0,
        sector_keywords=("construcció",),
    )


def _make_page_response(items: list[dict]) -> dict:
    return {
        "content": items,
        "totalPages": 1,
        "totalElements": len(items),
        "last": True,
        "empty": len(items) == 0,
    }


def _make_tender_item(expedient_id: str = "uuid-1") -> dict:
    return {
        "expedientId": expedient_id,
        "id": 42,
        "titol": "Obres de pavimentació",
        "organ": "Ajuntament de Girona",
        "pressupostLicitacio": 300_000.0,
        "codiExpedient": "EXP-001",
        "fase": "0",
        "dataPublicacio": "2026-05-01",
    }


class TestFetchPage:
    """Tests for ContractacioPublicaClient.fetch_page()."""

    @pytest.mark.asyncio
    async def test_returns_list_of_dicts(self):
        """fetch_page() must return a list of dicts."""
        client = ContractacioPublicaClient(base_url="http://mock", timeout=5)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = _make_page_response(
            [_make_tender_item()])

        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await client.fetch_page(_make_filter_config(), page=0)

        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_sends_correct_query_params(self):
        """fetch_page() must include tipusExpedient and faseVigent in the request."""
        client = ContractacioPublicaClient(base_url="http://mock", timeout=5)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = _make_page_response([])

        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            await client.fetch_page(_make_filter_config(), page=2)

        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs.args[1] if len(
            call_kwargs.args) > 1 else {}
        if not params and call_kwargs.kwargs:
            params = call_kwargs.kwargs.get("params", {})
        assert params.get("tipusExpedient") == 1
        assert params.get("faseVigent") == 0
        assert params.get("page") == 2

    @pytest.mark.asyncio
    async def test_raises_download_error_on_http_error(self):
        """fetch_page() must raise DownloadError on HTTP failure."""
        client = ContractacioPublicaClient(base_url="http://mock", timeout=5)

        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.RequestError("connection refused")
            with pytest.raises(DownloadError):
                await client.fetch_page(_make_filter_config(), page=0)

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_empty_page(self):
        """fetch_page() must return [] when API returns empty content."""
        client = ContractacioPublicaClient(base_url="http://mock", timeout=5)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = _make_page_response([])

        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await client.fetch_page(_make_filter_config(), page=0)

        assert result == []


class TestFetchDetail:
    """Tests for ContractacioPublicaClient.fetch_detail()."""

    @pytest.mark.asyncio
    async def test_returns_dict(self):
        """fetch_detail() must return a dict."""
        client = ContractacioPublicaClient(base_url="http://mock", timeout=5)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "expedientId": "uuid-1", "documents": []}

        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await client.fetch_detail("uuid-1", 42)

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_raises_download_error_on_http_error(self):
        """fetch_detail() must raise DownloadError on HTTP failure."""
        client = ContractacioPublicaClient(base_url="http://mock", timeout=5)

        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.RequestError("timeout")
            with pytest.raises(DownloadError):
                await client.fetch_detail("uuid-1", 42)


class TestDownloadDocument:
    """Tests for ContractacioPublicaClient.download_document()."""

    @pytest.mark.asyncio
    async def test_returns_bytes(self):
        """download_document() must return bytes."""
        client = ContractacioPublicaClient(base_url="http://mock", timeout=5)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b"%PDF-1.4 binary content"

        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await client.download_document(doc_id=99, doc_hash="abc123")

        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_raises_download_error_on_http_error(self):
        """download_document() must raise DownloadError on HTTP failure."""
        client = ContractacioPublicaClient(base_url="http://mock", timeout=5)

        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.RequestError("timeout")
            with pytest.raises(DownloadError):
                await client.download_document(doc_id=99, doc_hash="abc123")


class TestFetchDocuments:
    """Tests for ContractacioPublicaClient.fetch_documents()."""

    def _make_detail_response(self, docs: list[dict]) -> dict:
        """Build a mock /detall-publicacio-expedient response with nested docs."""
        return {
            "dades": {
                "dadesPublicacio": {
                    "documents": docs,
                },
            },
            "navegacioFases": [],
        }

    @pytest.mark.asyncio
    async def test_returns_list_of_documents(self):
        """fetch_documents() must return a list of dicts with id, titol, hash, mida."""
        client = ContractacioPublicaClient(base_url="http://mock", timeout=5)
        doc = {"id": 101, "titol": "PCAP.pdf", "hash": "abc123", "mida": 204800}
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = self._make_detail_response([doc])

        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await client.fetch_documents("uuid-1", 42)

        assert len(result) == 1
        assert result[0]["id"] == 101
        assert result[0]["titol"] == "PCAP.pdf"
        assert result[0]["hash"] == "abc123"

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_documents(self):
        """fetch_documents() must return [] when dades has no document nodes."""
        client = ContractacioPublicaClient(base_url="http://mock", timeout=5)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"dades": {}, "navegacioFases": []}

        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await client.fetch_documents("uuid-1", 42)

        assert result == []

    @pytest.mark.asyncio
    async def test_extracts_documents_recursively(self):
        """fetch_documents() must find documents nested at any depth in dades."""
        client = ContractacioPublicaClient(base_url="http://mock", timeout=5)
        nested_response = {
            "dades": {
                "dadesPublicacio": {
                    "seccio": {
                        "subseccio": {
                            "id": 202,
                            "titol": "PPT.pdf",
                            "hash": "def456",
                            "mida": 102400,
                        }
                    }
                },
                "documentFormalitzacio": {
                    "id": 303,
                    "titol": "Annex.pdf",
                    "hash": "ghi789",
                    "mida": 51200,
                },
            },
            "navegacioFases": [],
        }
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = nested_response

        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await client.fetch_documents("uuid-1", 42)

        ids = {d["id"] for d in result}
        assert 202 in ids
        assert 303 in ids

    @pytest.mark.asyncio
    async def test_raises_download_error_on_http_error(self):
        """fetch_documents() must raise DownloadError on HTTP failure."""
        client = ContractacioPublicaClient(base_url="http://mock", timeout=5)

        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.RequestError("timeout")
            with pytest.raises(DownloadError):
                await client.fetch_documents("uuid-1", 42)
