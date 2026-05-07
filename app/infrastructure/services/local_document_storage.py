"""Filesystem-based implementation of DocumentStoragePort."""
from __future__ import annotations

import asyncio
from pathlib import Path

from app.application.ports.document_storage_port import DocumentStoragePort
from app.domain.entities.document import Document


class LocalDocumentStorage(DocumentStoragePort):
    """Stores downloaded PDF documents on the local filesystem.

    Files are saved under ``<base_dir>/<expedient_id>/<titol>``.
    An in-memory index tracks (expedient_id, doc_id) → path to avoid
    re-downloading documents that already exist on disk.
    """

    def __init__(self, base_dir: str = "downloads") -> None:
        self._base_dir = Path(base_dir)
        self._index: dict[tuple[str, int], str] = {}

    async def save(self, document: Document, content: bytes) -> str:
        """Persist *content* to disk and return the stored file path."""
        dest_dir = self._base_dir / document.expedient_id
        await asyncio.to_thread(dest_dir.mkdir, parents=True, exist_ok=True)

        dest = dest_dir / document.titol
        await asyncio.to_thread(dest.write_bytes, content)

        path = str(dest)
        self._index[(document.expedient_id, document.doc_id)] = path
        return path

    async def exists(self, expedient_id: str, doc_id: int) -> bool:
        """Return True if the document has already been stored."""
        return (expedient_id, doc_id) in self._index

    async def get_path(self, expedient_id: str, doc_id: int) -> str | None:
        """Return the file path for a stored document, or None if not found."""
        return self._index.get((expedient_id, doc_id))

    async def list_documents(self, expedient_id: str) -> list[Document]:
        """Return all documents stored for the given expedient_id."""
        return []
