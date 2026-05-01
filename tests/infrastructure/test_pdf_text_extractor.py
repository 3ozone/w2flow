"""Tests for PdfTextExtractor infrastructure service."""

from __future__ import annotations

import pytest

pymupdf = pytest.importorskip("pymupdf", reason="pymupdf not installed")


def _make_pdf_bytes(text: str = "Hola món") -> bytes:
    """Generate a minimal valid PDF in memory containing the given text."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    return doc.tobytes()


class TestPdfTextExtractor:
    """Tests for PdfTextExtractor.

    Validates that PdfTextExtractor implements PdfExtractorPort and
    correctly extracts text from PDF bytes using pymupdf.
    """

    def _make_extractor(self):
        from app.infrastructure.services.pdf_text_extractor import PdfTextExtractor
        return PdfTextExtractor()

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def test_implements_pdf_extractor_port(self):
        """PdfTextExtractor must implement PdfExtractorPort."""
        from app.application.ports.pdf_extractor_port import PdfExtractorPort
        extractor = self._make_extractor()
        assert isinstance(extractor, PdfExtractorPort)

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------

    def test_extracts_text_from_single_page_pdf(self):
        """extract_text() must return the text content of a single-page PDF."""
        extractor = self._make_extractor()
        pdf_bytes = _make_pdf_bytes("Plec de clàusules administratives")
        result = extractor.extract_text(pdf_bytes)
        assert "Plec" in result
        assert "clàusules" in result

    def test_extracts_text_from_multipage_pdf(self):
        """extract_text() must concatenate text from all pages."""
        doc = pymupdf.open()
        page1 = doc.new_page()
        page1.insert_text((72, 72), "Pàgina u")
        page2 = doc.new_page()
        page2.insert_text((72, 72), "Pàgina dos")
        pdf_bytes = doc.tobytes()

        extractor = self._make_extractor()
        result = extractor.extract_text(pdf_bytes)
        assert "Pàgina u" in result
        assert "Pàgina dos" in result

    def test_returns_string(self):
        """extract_text() must return a str."""
        extractor = self._make_extractor()
        result = extractor.extract_text(_make_pdf_bytes("test"))
        assert isinstance(result, str)

    def test_empty_pdf_returns_empty_or_whitespace(self):
        """extract_text() on a PDF with no text must return empty string or whitespace."""
        doc = pymupdf.open()
        doc.new_page()  # blank page, no text
        pdf_bytes = doc.tobytes()

        extractor = self._make_extractor()
        result = extractor.extract_text(pdf_bytes)
        assert result.strip() == ""
