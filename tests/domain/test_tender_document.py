"""Tests per a l'entitat de domini TenderDocument (Fase J.2, RF-09, RF-10)."""
from datetime import datetime, timezone

import pytest

from app.domain.entities.tender_document import TenderDocument


_NOW = datetime(2026, 5, 13, 10, 0, 0, tzinfo=timezone.utc)


def _make_doc(**kwargs) -> TenderDocument:
    """Helper: crea un TenderDocument mínim sobreescrivint només els camps indicats."""
    defaults = {
        "expedient_id": "exp-001",
        "filename": "PCAP.pdf",
        "filepath": "downloads/exp-001/PCAP.pdf",
        "comentari_llm": None,
        "created_at": _NOW,
    }
    defaults.update(kwargs)
    return TenderDocument(**defaults)


class TestTenderDocumentCreation:
    """Tests per a la creació i validació d'instàncies de TenderDocument."""

    def test_crea_document_sense_comentari(self):
        """Ha de crear un document sense comentari LLM sense llançar cap error."""
        doc = _make_doc()
        assert doc.expedient_id == "exp-001"
        assert doc.filename == "PCAP.pdf"
        assert doc.comentari_llm is None

    def test_crea_document_amb_comentari_llm(self):
        """Ha d'acceptar i emmagatzemar un comentari LLM no nul."""
        doc = _make_doc(
            comentari_llm="El PCAP conté criteris de solvència ben definits.")
        assert doc.comentari_llm == "El PCAP conté criteris de solvència ben definits."

    def test_te_comentari_retorna_false_sense_comentari(self):
        """te_comentari() ha de retornar False quan comentari_llm és None."""
        doc = _make_doc(comentari_llm=None)
        assert doc.te_comentari() is False

    def test_te_comentari_retorna_true_amb_comentari(self):
        """te_comentari() ha de retornar True quan comentari_llm té valor."""
        doc = _make_doc(comentari_llm="Comentari.")
        assert doc.te_comentari() is True

    def test_filename_no_pot_ser_buit(self):
        """Ha de llançar ValueError si filename és una cadena buida."""
        with pytest.raises(ValueError, match="filename"):
            _make_doc(filename="")

    def test_expedient_id_no_pot_ser_buit(self):
        """Ha de llançar ValueError si expedient_id és una cadena buida."""
        with pytest.raises(ValueError, match="expedient_id"):
            _make_doc(expedient_id="")
