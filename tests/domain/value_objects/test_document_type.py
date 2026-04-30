import pytest

from app.domain.value_objects.document_type import DocumentType


class TestDocumentType:
    """Tests for the DocumentType enum."""

    def test_pcap_value_exists(self):
        """PCAP (Pliego de Cláusulas Administrativas Particulares) member must exist."""
        assert DocumentType.PCAP is not None

    def test_ppt_value_exists(self):
        """PPT (Pliego de Prescripciones Técnicas) member must exist."""
        assert DocumentType.PPT is not None

    def test_technical_memory_value_exists(self):
        """TECHNICAL_MEMORY member must exist."""
        assert DocumentType.TECHNICAL_MEMORY is not None

    def test_budget_value_exists(self):
        """BUDGET member must exist."""
        assert DocumentType.BUDGET is not None

    def test_annexes_value_exists(self):
        """ANNEXES member must exist."""
        assert DocumentType.ANNEXES is not None

    def test_unknown_value_exists(self):
        """UNKNOWN member must exist for documents whose title cannot be classified."""
        assert DocumentType.UNKNOWN is not None

    def test_all_values_are_unique(self):
        """Every enum value must be unique to avoid aliasing."""
        values = [e.value for e in DocumentType]
        assert len(values) == len(set(values))

    def test_has_exactly_six_members(self):
        """Enum must contain exactly the six document types (five named + UNKNOWN)."""
        assert len(DocumentType) == 6

    def test_from_title_pcap(self):
        """from_title() must return PCAP when the title contains 'pcap'."""
        assert DocumentType.from_title("PCAP_expedient_123.pdf") == DocumentType.PCAP

    def test_from_title_ppt(self):
        """from_title() must return PPT when the title contains 'ppt'."""
        assert DocumentType.from_title("PPT_obra_civil.pdf") == DocumentType.PPT

    def test_from_title_technical_memory(self):
        """from_title() must return TECHNICAL_MEMORY for memory-related titles."""
        assert DocumentType.from_title("Memoria_tecnica.pdf") == DocumentType.TECHNICAL_MEMORY

    def test_from_title_budget(self):
        """from_title() must return BUDGET for budget-related titles."""
        assert DocumentType.from_title("Pressupost_base.pdf") == DocumentType.BUDGET

    def test_from_title_annexes(self):
        """from_title() must return ANNEXES for annex-related titles."""
        assert DocumentType.from_title("Annex_I_criteris.pdf") == DocumentType.ANNEXES

    def test_from_title_unknown(self):
        """from_title() must return UNKNOWN when the title does not match any known type."""
        assert DocumentType.from_title("document_sense_classificar.pdf") == DocumentType.UNKNOWN

    def test_from_title_is_case_insensitive(self):
        """from_title() must be case-insensitive."""
        assert DocumentType.from_title("pcap_expedient.pdf") == DocumentType.PCAP
        assert DocumentType.from_title("PCAP_expedient.pdf") == DocumentType.PCAP
