"""Port (contracte ABC) per persistir documents adjunts de licitacions a disc (RF-09)."""
from abc import ABC, abstractmethod

from app.domain.entities.tender_document import TenderDocument


class DocumentStoragePort(ABC):
    """Defineix el contracte per guardar i recuperar documents PDF d'una licitació.

    La infraestructura implementarà aquest port amb emmagatzematge local (RF-09).
    """

    @abstractmethod
    def save(self, expedient_id: str, filename: str, content: bytes) -> TenderDocument:
        """Desa un document PDF a disc i retorna l'entitat TenderDocument creada.

        Args:
            expedient_id: UUID de la licitació a la qual pertany el document.
            filename:     Nom del fitxer (p. ex. ``PCAP.pdf``).
            content:      Contingut binari del PDF.

        Returns:
            TenderDocument amb la ruta relativa al fitxer desat i la data de creació.
        """

    @abstractmethod
    def list_documents(self, expedient_id: str) -> list[str]:
        """Retorna els noms dels fitxers desats per a un expedient.

        Args:
            expedient_id: UUID de la licitació.

        Returns:
            Llista de noms de fitxer (p. ex. ``["PCAP.pdf", "PPT.pdf"]``).
        """

    @abstractmethod
    def delete(self, expedient_id: str, filename: str) -> None:
        """Elimina un document del disc.

        Args:
            expedient_id: UUID de la licitació.
            filename:     Nom del fitxer a eliminar.
        """
