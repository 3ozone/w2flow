"""SQLAlchemy implementation of DocumentStoragePort."""

from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy.orm import Session

from app.application.ports.document_storage_port import DocumentStoragePort
from app.domain.entities.document import Document
from app.infrastructure.repositories.models import DocumentModel


class DocumentRepository(DocumentStoragePort):
    """Persists and retrieves Documents: writes PDF to disk and metadata to DB.

    Deduplication (RN-06): saving a document that already exists is idempotent
    — it overwrites the file on disk, updates the DB record and returns the path.
    """

    def __init__(self, session: Session, base_dir: str | Path = "downloads") -> None:
        self._session = session
        self._base_dir = Path(base_dir)

    async def save(self, document: Document, content: bytes) -> str:
        """Write PDF bytes to disk and persist metadata to DB. Returns the file path."""
        dest_dir = self._base_dir / document.expedient_id
        await asyncio.to_thread(dest_dir.mkdir, parents=True, exist_ok=True)
        dest = dest_dir / document.titol
        await asyncio.to_thread(dest.write_bytes, content)
        file_path = str(dest)

        existing = self._session.get(
            DocumentModel, (document.expedient_id, document.doc_id)
        )
        if existing is not None:
            existing.titol = document.titol
            existing.hash = document.hash
            existing.mida_kb = document.mida_kb
            existing.file_path = file_path
            existing.type = document.type.value
            self._session.flush()
            return file_path

        model = DocumentModel(
            expedient_id=document.expedient_id,
            doc_id=document.doc_id,
            titol=document.titol,
            hash=document.hash,
            mida_kb=document.mida_kb,
            file_path=file_path,
            type=document.type.value,
        )
        self._session.add(model)
        self._session.flush()
        return file_path

    async def exists(self, expedient_id: str, doc_id: int) -> bool:
        """Return True if the document has already been stored."""
        model = self._session.get(DocumentModel, (expedient_id, doc_id))
        return model is not None

    async def get_path(self, expedient_id: str, doc_id: int) -> str | None:
        """Return the file path for a stored document, or None if not found."""
        model = self._session.get(DocumentModel, (expedient_id, doc_id))
        if model is None:
            return None
        return model.file_path
