"""Port (contrato ABC) per analitzar documents PDF amb NLP via Timbal (RF-05, RN-12)."""
from abc import ABC, abstractmethod

from app.domain.entities.document_analysis import DocumentAnalysis


class NlpAnalyserPort(ABC):
    """Defineix el contracte que ha de complir qualsevol analitzador NLP.

    La infraestructura implementarà aquest port amb Timbal (RF-05).
    Rep els bytes dels PDFs obligatoris d'una licitació i retorna la puntuació.
    """

    @abstractmethod
    def analyse(
        self,
        expedient_id: str,
        documents: list[bytes],
        filenames: list[str] | None = None,
    ) -> DocumentAnalysis:
        """Analitza els documents PDF d'una licitació i retorna la puntuació NLP (RN-12).

        Args:
            expedient_id: Identificador únic de l'expedient analitzat.
            documents:    Llista de continguts binaris dels PDFs obligatoris (PCAP, PPT, memòria).
            filenames:    Noms dels fitxers en el mateix ordre que documents,
                          usats pel LLM per generar comentaris_per_doc (RF-10).

        Returns:
            DocumentAnalysis amb les puntuacions per cada criteri i comentaris narratius.
        """
