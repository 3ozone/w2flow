"""Unit tests for the Document entity."""
import pytest

from app.domain.entities.document import Document
from app.domain.value_objects.document_type import DocumentType


class TestDocument:
    """Tests for the Document entity."""

    def _make_document(self, **kwargs) -> Document:
        """Helper to build a Document instance with sensible defaults."""
        defaults = {
            "expedient_id": "uuid-abc-123",
            "doc_id": 10,
            "titol": "Plec de Clàusules Administratives Particulars",
            "hash": "abc123def456",
            "mida_kb": 512.0,
            "file_path": "/downloads/uuid-abc-123/pcap.pdf",
            "type": DocumentType.PCAP,
        }
        defaults.update(kwargs)
        return Document(**defaults)

    # ------------------------------------------------------------------
    # is_valid_type()
    # ------------------------------------------------------------------

    def test_is_valid_type_returns_true_for_pcap(self):
        """is_valid_type() must return True when type is PCAP."""
        doc = self._make_document(type=DocumentType.PCAP)
        assert doc.is_valid_type() is True

    def test_is_valid_type_returns_true_for_ppt(self):
        """is_valid_type() must return True when type is PPT."""
        doc = self._make_document(type=DocumentType.PPT)
        assert doc.is_valid_type() is True

    def test_is_valid_type_returns_true_for_technical_memory(self):
        """is_valid_type() must return True when type is TECHNICAL_MEMORY."""
        doc = self._make_document(type=DocumentType.TECHNICAL_MEMORY)
        assert doc.is_valid_type() is True

    def test_is_valid_type_returns_true_for_budget(self):
        """is_valid_type() must return True when type is BUDGET."""
        doc = self._make_document(type=DocumentType.BUDGET)
        assert doc.is_valid_type() is True

    def test_is_valid_type_returns_true_for_annexes(self):
        """is_valid_type() must return True when type is ANNEXES."""
        doc = self._make_document(type=DocumentType.ANNEXES)
        assert doc.is_valid_type() is True

    def test_is_valid_type_returns_false_for_unknown(self):
        """is_valid_type() must return False when type is UNKNOWN."""
        doc = self._make_document(type=DocumentType.UNKNOWN)
        assert doc.is_valid_type() is False

    # ------------------------------------------------------------------
    # Identity by (expedient_id, doc_id)
    # ------------------------------------------------------------------

    def test_equality_same_expedient_and_doc_id(self):
        """Two Documents with the same (expedient_id, doc_id) must be equal."""
        a = self._make_document()
        b = self._make_document(titol="Títol diferent", hash="other-hash")
        assert a == b

    def test_equality_different_doc_id(self):
        """Two Documents with different doc_id must not be equal."""
        a = self._make_document(doc_id=10)
        b = self._make_document(doc_id=99)
        assert a != b

    def test_equality_different_expedient_id(self):
        """Two Documents with different expedient_id must not be equal."""
        a = self._make_document(expedient_id="uuid-aaa")
        b = self._make_document(expedient_id="uuid-bbb")
        assert a != b

    def test_hash_by_expedient_and_doc_id(self):
        """Two Documents with the same (expedient_id, doc_id) must have same hash."""
        a = self._make_document()
        b = self._make_document(titol="Títol diferent")
        assert hash(a) == hash(b)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_empty_expedient_id_raises(self):
        """Document must raise ValueError if expedient_id is empty."""
        with pytest.raises(ValueError):
            self._make_document(expedient_id="")

    def test_empty_titol_raises(self):
        """Document must raise ValueError if titol is empty."""
        with pytest.raises(ValueError):
            self._make_document(titol="")

    def test_negative_mida_kb_raises(self):
        """Document must raise ValueError if mida_kb is negative."""
        with pytest.raises(ValueError):
            self._make_document(mida_kb=-1.0)
