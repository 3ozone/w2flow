"""SQLAlchemy implementation of DocumentStoragePort."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.ports.document_storage_port import DocumentStoragePort
from app.domain.entities.document import Document
from app.infrastructure.repositories.models import DocumentModel


class DocumentRepository(DocumentStoragePort):
    """Persists and retrieves Documents using SQLAlchemy.

    Deduplication (RN-06): saving a document that already exists is idempotent
    — it updates the record in place and returns the stored file path.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    async def save(self, document: Document, content: bytes) -> str:
        """Persist document metadata. Returns the stored file path."""
        existing = self._session.get(
            DocumentModel, (document.expedient_id, document.doc_id)
        )
        if existing is not None:
            # Idempotent: update fields and return existing path
            existing.titol = document.titol
            existing.hash = document.hash
            existing.mida_kb = document.mida_kb
            existing.file_path = document.file_path
            existing.type = document.type.value
            self._session.flush()
            return existing.file_path

        model = DocumentModel(
            expedient_id=document.expedient_id,
            doc_id=document.doc_id,
            titol=document.titol,
            hash=document.hash,
            mida_kb=document.mida_kb,
            file_path=document.file_path,
            type=document.type.value,
        )
        self._session.add(model)
        self._session.flush()
        return model.file_path

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
