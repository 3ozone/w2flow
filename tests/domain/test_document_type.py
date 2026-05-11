"""Tests for DocumentType value object (RN-02)."""
from app.domain.value_objects.document_type import DocumentType


def test_mandatory_types_exist():
    """Los 5 tipos obligatorios definidos en RN-02 deben existir en el enum."""
    assert DocumentType.PCAP
    assert DocumentType.PPT
    assert DocumentType.TECHNICAL_MEMORY
    assert DocumentType.BUDGET
    assert DocumentType.ANNEXES


def test_from_api_section_pcap():
    """La sección 'plecsDeClausulesAdministratives' se clasifica como PCAP."""
    assert DocumentType.from_api_section(
        "plecsDeClausulesAdministratives") == DocumentType.PCAP


def test_from_api_section_ppt():
    """La sección 'plecsDePrescripcionsTecniques' se clasifica como PPT."""
    assert DocumentType.from_api_section(
        "plecsDePrescripcionsTecniques") == DocumentType.PPT


def test_from_api_section_memory():
    """La sección 'memoriaJustificativaContracte' se clasifica como TECHNICAL_MEMORY."""
    assert DocumentType.from_api_section(
        "memoriaJustificativaContracte") == DocumentType.TECHNICAL_MEMORY


def test_from_api_section_unknown():
    """Una sección no mapeada devuelve UNKNOWN."""
    assert DocumentType.from_api_section(
        "altresDocuments") == DocumentType.UNKNOWN
