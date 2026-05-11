"""Port (contrato ABC) per persistir licitacions a la base de dades (RN-06)."""
from abc import ABC, abstractmethod

from app.domain.entities.tender import Tender


class TenderRepositoryPort(ABC):
    """Defineix el contracte que ha de complir qualsevol repositori de licitacions.

    La infraestructura implementarà aquest port (SQLAlchemy).
    Permet descartar duplicats abans de processar una licitació.
    """

    @abstractmethod
    def is_duplicate(self, expedient_id: str) -> bool:
        """Comprova si una licitació ja ha estat processada anteriorment (RN-06).

        Args:
            expedient_id: Identificador únic de l'expedient.

        Returns:
            True si ja existeix a la base de dades, False en cas contrari.
        """

    @abstractmethod
    def save(self, tender: Tender) -> None:
        """Persisteix una licitació a la base de dades.

        Args:
            tender: Entitat Tender a guardar.
        """

    @abstractmethod
    def list_all(self) -> list[Tender]:
        """Retorna totes les licitacions persistides a la base de dades.

        Returns:
            Llista de Tender ordenada de més recent a més antiga.
        """

    @abstractmethod
    def count(self) -> int:
        """Retorna el nombre total de licitacions persistides a la base de dades.

        Returns:
            Nombre enter de registres existents.
        """
