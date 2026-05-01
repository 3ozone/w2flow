"""Unit tests for DocumentDTO."""

from app.application.dtos.document_dto import DocumentDTO
from app.domain.entities.document import Document
from app.domain.value_objects.document_type import DocumentType


class TestDocumentDTO:
    """Tests for DocumentDTO — conversion between domain and application layer."""

    def _make_document(self, **kwargs) -> Document:
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
    # from_domain()
    # ------------------------------------------------------------------

    def test_from_domain_preserves_expedient_id(self):
        """from_domain() must preserve expedient_id."""
        dto = DocumentDTO.from_domain(self._make_document())
        assert dto.expedient_id == "uuid-abc-123"

    def test_from_domain_preserves_doc_id(self):
        """from_domain() must preserve doc_id."""
        dto = DocumentDTO.from_domain(self._make_document())
        assert dto.doc_id == 10

    def test_from_domain_preserves_titol(self):
        """from_domain() must preserve titol."""
        dto = DocumentDTO.from_domain(self._make_document())
        assert dto.titol == "Plec de Clàusules Administratives Particulars"

    def test_from_domain_preserves_hash(self):
        """from_domain() must preserve hash."""
        dto = DocumentDTO.from_domain(self._make_document())
        assert dto.hash == "abc123def456"

    def test_from_domain_preserves_mida_kb(self):
        """from_domain() must preserve mida_kb."""
        dto = DocumentDTO.from_domain(self._make_document())
        assert dto.mida_kb == 512.0

    def test_from_domain_preserves_file_path(self):
        """from_domain() must preserve file_path."""
        dto = DocumentDTO.from_domain(self._make_document())
        assert dto.file_path == "/downloads/uuid-abc-123/pcap.pdf"

    def test_from_domain_serializes_type_as_string(self):
        """from_domain() must serialize DocumentType as its string value."""
        dto = DocumentDTO.from_domain(
            self._make_document(type=DocumentType.PPT))
        assert dto.type == DocumentType.PPT.value

    # ------------------------------------------------------------------
    # to_domain()
    # ------------------------------------------------------------------

    def test_to_domain_returns_document_instance(self):
        """to_domain() must return a Document instance."""
        dto = DocumentDTO.from_domain(self._make_document())
        assert isinstance(dto.to_domain(), Document)

    def test_to_domain_parses_type_from_string(self):
        """to_domain() must parse type string back to DocumentType enum."""
        doc = self._make_document(type=DocumentType.BUDGET)
        assert DocumentDTO.from_domain(
            doc).to_domain().type == DocumentType.BUDGET

    def test_to_domain_preserves_expedient_id(self):
        """to_domain() must preserve expedient_id."""
        doc = self._make_document()
        assert DocumentDTO.from_domain(
            doc).to_domain().expedient_id == doc.expedient_id

    # ------------------------------------------------------------------
    # Roundtrip
    # ------------------------------------------------------------------

    def test_roundtrip_from_domain_to_domain(self):
        """from_domain() followed by to_domain() must produce an equal Document."""
        doc = self._make_document()
        assert DocumentDTO.from_domain(doc).to_domain() == doc

    def test_roundtrip_all_document_types(self):
        """Roundtrip must work for all valid DocumentType values."""
        for doc_type in DocumentType:
            doc = self._make_document(type=doc_type)
            assert DocumentDTO.from_domain(doc).to_domain().type == doc_type
