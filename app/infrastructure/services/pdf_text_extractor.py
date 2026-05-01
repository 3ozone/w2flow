"""PDF text extraction service using pymupdf."""

from __future__ import annotations

import pymupdf

from app.application.ports.pdf_extractor_port import PdfExtractorPort


class PdfTextExtractor(PdfExtractorPort):
    """Extracts text from PDF bytes using pymupdf."""

    def extract_text(self, pdf_bytes: bytes) -> str:
        """Return the concatenated text from all pages of the PDF."""
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        pages_text = [page.get_text() for page in doc]
        return "\n".join(pages_text)
