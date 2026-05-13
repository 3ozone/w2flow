"""Tests for Document entity (RF-04, RN-02)."""
from app.domain.entities.document import Document
from app.domain.value_objects.document_type import DocumentType


def _make_document(**kwargs) -> Document:
    """Helper: crea un Document mínim sobreescrivint els camps indicats."""
    defaults = {
        "expedient_id": "f0b5b0e9-474a-482f-b917-908b85d2ca97",
        "doc_id": 302221234,
        "titol": "PCAP CONTRACTE SERVEI SOCORRISME PISCINA 2026.pdf",
        "hash": "4E5107C93071F4E9FF6AEB836FE8D0BE",
        "mida": 553366,
        "doc_type": DocumentType.PCAP,
    }
    defaults.update(kwargs)
    return Document(**defaults)


def test_is_mandatory_pcap():
    """PCAP és un document obligatori (RN-02)."""
    doc = _make_document(doc_type=DocumentType.PCAP)
    assert doc.is_mandatory() is True


def test_is_mandatory_ppt():
    """PPT és un document obligatori (RN-02)."""
    doc = _make_document(doc_type=DocumentType.PPT)
    assert doc.is_mandatory() is True


def test_is_not_mandatory_unknown():
    """Un document de tipus UNKNOWN no és obligatori (RN-02)."""
    doc = _make_document(doc_type=DocumentType.UNKNOWN)
    assert doc.is_mandatory() is False
