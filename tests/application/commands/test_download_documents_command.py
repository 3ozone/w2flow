"""Tests for DownloadDocumentsCommandHandler."""

from __future__ import annotations

from unittest.mock import AsyncMock
import pytest

from app.application.use_cases.commands.download_documents_command import (
    DownloadDocumentsCommand,
    DownloadDocumentsCommandHandler,
)
from app.domain.entities.document import Document
from app.domain.entities.tender import Tender
from datetime import date


def _make_tender(expedient_id: str = "uuid-1") -> Tender:
    return Tender(
        expedient_id=expedient_id,
        publicacio_id=42,
        titol="Obres de pavimentació",
        organ="Ajuntament de Girona",
        pressupost=500_000.0,
        codi_expedient="EXP-001",
        fase="0",
        data_publicacio=date.today(),
    )


def _make_doc_dict(doc_id: int = 1, titol: str = "PCAP_exp.pdf", doc_hash: str = "abc123") -> dict:
    return {
        "id": doc_id,
        "titol": titol,
        "hash": doc_hash,
        "midaKb": 120.5,
    }


class TestDownloadDocumentsCommandHandler:
    """Tests for DownloadDocumentsCommandHandler.

    Validates that the handler fetches documents from the API, downloads
    valid-typed PDFs and persists them via DocumentStoragePort.
    """

    def _make_handler(
        self,
        api_docs: list[dict] | None = None,
        pdf_bytes: bytes = b"%PDF-1.4 fake",
    ):
        api = AsyncMock()
        api.fetch_documents.return_value = api_docs if api_docs is not None else []
        api.download_document.return_value = pdf_bytes

        storage = AsyncMock()
        storage.exists.return_value = False
        storage.save.return_value = "downloads/uuid-1/doc.pdf"

        tender = _make_tender()
        handler = DownloadDocumentsCommandHandler(api=api, storage=storage)
        command = DownloadDocumentsCommand(tender=tender)
        return handler, command, api, storage

    # ------------------------------------------------------------------
    # Return type
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_returns_list_of_documents(self):
        """handle() must return a list of (Document, bytes|None) tuples."""
        handler, command, _, _ = self._make_handler(
            api_docs=[_make_doc_dict(titol="PCAP_exp.pdf")]
        )
        result = await handler.handle(command)
        assert isinstance(result, list)
        assert all(isinstance(doc, Document) for doc, _ in result)

    # ------------------------------------------------------------------
    # Filtering by DocumentType
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_skips_unknown_document_types(self):
        """Documents with UNKNOWN type must not be downloaded nor returned."""
        handler, command, api, storage = self._make_handler(
            api_docs=[
                _make_doc_dict(doc_id=1, titol="PCAP_exp.pdf"),
                _make_doc_dict(
                    doc_id=2, titol="Fotografia_acte.jpg"),  # UNKNOWN
            ]
        )
        result = await handler.handle(command)
        assert len(result) == 1
        assert result[0][0].doc_id == 1
        assert api.download_document.call_count == 1

    @pytest.mark.asyncio
    async def test_downloads_all_valid_types(self):
        """All non-UNKNOWN document types must be downloaded."""
        handler, command, api, _ = self._make_handler(
            api_docs=[
                _make_doc_dict(doc_id=1, titol="PCAP_exp.pdf"),
                _make_doc_dict(doc_id=2, titol="PPT_exp.pdf"),
                _make_doc_dict(doc_id=3, titol="Memoria_tecnica.pdf"),
            ]
        )
        result = await handler.handle(command)
        assert len(result) == 3
        assert api.download_document.call_count == 3

    # ------------------------------------------------------------------
    # Deduplication
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_skips_already_stored_documents(self):
        """Documents that already exist in storage must not be re-downloaded."""
        api = AsyncMock()
        api.fetch_documents.return_value = [
            _make_doc_dict(doc_id=1, titol="PCAP_exp.pdf")]
        api.download_document.return_value = b"%PDF"

        storage = AsyncMock()
        storage.exists.return_value = True  # already stored
        storage.get_path.return_value = "downloads/uuid-1/PCAP_exp.pdf"

        handler = DownloadDocumentsCommandHandler(api=api, storage=storage)
        command = DownloadDocumentsCommand(tender=_make_tender())
        result = await handler.handle(command)

        api.download_document.assert_not_called()
        assert len(result) == 1
        assert result[0][0].file_path == "downloads/uuid-1/PCAP_exp.pdf"

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_persists_document_via_storage(self):
        """handle() must call storage.save() for each downloaded document."""
        handler, command, _, storage = self._make_handler(
            api_docs=[_make_doc_dict(titol="PCAP_exp.pdf")]
        )
        await handler.handle(command)
        storage.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_returned_document_has_correct_file_path(self):
        """Returned Document.file_path must match what storage.save() returned."""
        expected_path = "downloads/uuid-1/PCAP_exp.pdf"
        api = AsyncMock()
        api.fetch_documents.return_value = [
            _make_doc_dict(titol="PCAP_exp.pdf")]
        api.download_document.return_value = b"%PDF"

        storage = AsyncMock()
        storage.exists.return_value = False
        storage.save.return_value = expected_path

        handler = DownloadDocumentsCommandHandler(api=api, storage=storage)
        command = DownloadDocumentsCommand(tender=_make_tender())
        result = await handler.handle(command)

        assert result[0][0].file_path == expected_path

    # ------------------------------------------------------------------
    # Empty API response
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_empty_api_returns_empty_list(self):
        """When the API returns no documents, handle() must return an empty list."""
        handler, command, _, _ = self._make_handler(api_docs=[])
        result = await handler.handle(command)
        assert result == []
