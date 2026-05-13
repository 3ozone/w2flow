"""Port (contracte ABC) per persistir i consultar documents adjunts de licitacions (RF-09)."""
from abc import ABC, abstractmethod

from app.domain.entities.tender_document import TenderDocument


class TenderDocumentRepositoryPort(ABC):
    """Defineix el contracte per guardar i recuperar TenderDocument a la base de dades."""

    @abstractmethod
    def save(self, document: TenderDocument) -> None:
        """Persisteix un document adjunt a la base de dades.

        Args:
            document: Entitat TenderDocument a guardar.
        """

    @abstractmethod
    def list_by_expedient(self, expedient_id: str) -> list[TenderDocument]:
        """Retorna tots els documents d'un expedient ordenats per nom de fitxer.

        Args:
            expedient_id: UUID de la licitació.

        Returns:
            Llista de TenderDocument, buida si no n'hi ha cap.
        """

    @abstractmethod
    def update_comentari(self, expedient_id: str, filename: str, comentari: str) -> None:
        """Actualitza el comentari LLM d'un document adjunt.

        Args:
            expedient_id: UUID de la licitació.
            filename:     Nom del fitxer PDF.
            comentari:    Comentari narratiu generat pel LLM (RF-10).
        """
