"""Port (interface) for PDF text extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PdfExtractorPort(ABC):
    """Abstract contract for extracting text from PDF bytes."""

    @abstractmethod
    def extract_text(self, pdf_bytes: bytes) -> str:
        """Extract and return the concatenated text from all pages of a PDF."""
