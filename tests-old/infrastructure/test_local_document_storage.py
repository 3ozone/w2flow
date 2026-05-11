"""Tests for LocalDocumentStorage — filesystem-based DocumentStoragePort."""
from __future__ import annotations

import pytest

from app.domain.entities.document import Document
from app.domain.value_objects.document_type import DocumentType


def _make_document(expedient_id: str = "exp-001", doc_id: int = 1, titol: str = "plec.pdf") -> Document:
    return Document(
        expedient_id=expedient_id,
        doc_id=doc_id,
        titol=titol,
        hash="abc123",
        mida_kb=10.0,
        file_path="",
        type=DocumentType.PCAP,
    )


class TestLocalDocumentStorage:
    """Unit tests for LocalDocumentStorage."""

    @pytest.mark.asyncio
    async def test_save_writes_file_to_disk(self, tmp_path):
        """save() persists bytes under <base_dir>/<expedient_id>/<titol>."""
        from app.infrastructure.services.local_document_storage import LocalDocumentStorage

        storage = LocalDocumentStorage(base_dir=str(tmp_path))
        doc = _make_document()
        content = b"%PDF-1.4 fake content"

        path = await storage.save(doc, content)

        expected = tmp_path / "exp-001" / "plec.pdf"
        assert expected.exists()
        assert expected.read_bytes() == content
        assert path == str(expected)

    @pytest.mark.asyncio
    async def test_save_returns_stored_file_path(self, tmp_path):
        """save() returns the absolute path where the file was written."""
        from app.infrastructure.services.local_document_storage import LocalDocumentStorage

        storage = LocalDocumentStorage(base_dir=str(tmp_path))
        doc = _make_document(titol="memoria.pdf")
        path = await storage.save(doc, b"data")

        assert path.endswith("memoria.pdf")
        assert "exp-001" in path

    @pytest.mark.asyncio
    async def test_exists_returns_false_before_save(self, tmp_path):
        """exists() returns False when no file has been stored yet."""
        from app.infrastructure.services.local_document_storage import LocalDocumentStorage

        storage = LocalDocumentStorage(base_dir=str(tmp_path))
        result = await storage.exists("exp-001", 1)

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_returns_true_after_save(self, tmp_path):
        """exists() returns True after save() has been called."""
        from app.infrastructure.services.local_document_storage import LocalDocumentStorage

        storage = LocalDocumentStorage(base_dir=str(tmp_path))
        doc = _make_document()
        await storage.save(doc, b"data")

        result = await storage.exists("exp-001", 1)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_path_returns_none_before_save(self, tmp_path):
        """get_path() returns None when the document does not exist."""
        from app.infrastructure.services.local_document_storage import LocalDocumentStorage

        storage = LocalDocumentStorage(base_dir=str(tmp_path))
        result = await storage.get_path("exp-001", 1)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_path_returns_path_after_save(self, tmp_path):
        """get_path() returns the stored path after save()."""
        from app.infrastructure.services.local_document_storage import LocalDocumentStorage

        storage = LocalDocumentStorage(base_dir=str(tmp_path))
        doc = _make_document()
        saved_path = await storage.save(doc, b"data")

        result = await storage.get_path("exp-001", 1)

        assert result == saved_path

    @pytest.mark.asyncio
    async def test_save_creates_intermediate_directories(self, tmp_path):
        """save() creates the expedient subdirectory if it does not exist."""
        from app.infrastructure.services.local_document_storage import LocalDocumentStorage

        storage = LocalDocumentStorage(base_dir=str(tmp_path))
        doc = _make_document(expedient_id="new-exp-999")

        await storage.save(doc, b"data")

        assert (tmp_path / "new-exp-999").is_dir()
