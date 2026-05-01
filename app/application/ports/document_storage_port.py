"""Port (interface) for document file storage."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.document import Document


class DocumentStoragePort(ABC):
    """Abstract contract for storing and retrieving downloaded documents."""

    @abstractmethod
    async def save(self, document: Document, content: bytes) -> str:
        """Persist document bytes and return the stored file path."""

    @abstractmethod
    async def exists(self, expedient_id: str, doc_id: int) -> bool:
        """Return True if the document has already been stored."""

    @abstractmethod
    async def get_path(self, expedient_id: str, doc_id: int) -> str | None:
        """Return the file path for a stored document, or None if not found."""
