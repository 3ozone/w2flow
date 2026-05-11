"""Port (interface) for tender persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.document import Document
from app.domain.entities.tender import Tender
from app.domain.entities.scored_tender import ScoredTender


class TenderRepositoryPort(ABC):
    """Abstract contract for persisting and retrieving tenders."""

    @abstractmethod
    async def save(self, tender: Tender) -> None:
        """Persist a tender. Raises DuplicateTenderError if already exists."""

    @abstractmethod
    async def get_by_id(self, expedient_id: str) -> Tender | None:
        """Return the tender with the given expedient_id, or None."""

    @abstractmethod
    async def save_scored(self, scored_tender: ScoredTender) -> None:
        """Persist a scored tender."""

    @abstractmethod
    async def list_scored(self, page: int = 0, size: int = 20) -> list[ScoredTender]:
        """Return a paginated list of scored tenders."""

    @abstractmethod
    async def list_documents(self, expedient_id: str) -> list[Document]:
        """Return all documents stored for the given expedient_id."""

    @abstractmethod
    async def delete(self, expedient_id: str) -> None:
        """Delete a tender and all its associated scores and documents."""
