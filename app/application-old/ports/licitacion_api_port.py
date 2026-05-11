"""Port (interface) for the external licitacion API client."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.value_objects.filter_config import FilterConfig


class LicitationApiPort(ABC):
    """Abstract contract for fetching tenders from the external API."""

    @abstractmethod
    async def fetch_page(self, filter_config: FilterConfig, page: int) -> list[dict]:
        """Fetch a single page of tender summaries from the API."""

    @abstractmethod
    async def fetch_detail(self, expedient_id: str, publicacio_id: int) -> dict:
        """Fetch full detail for a single tender."""

    @abstractmethod
    async def fetch_documents(self, expedient_id: str, publicacio_id: int) -> list[dict]:
        """Return the list of downloadable documents for a tender."""

    @abstractmethod
    async def download_document(self, doc_id: int, doc_hash: str) -> bytes:
        """Download the raw PDF bytes for a document."""
