"""Port (contrato ABC) per persistir i recuperar configuracions de filtre (RF-03)."""
from abc import ABC, abstractmethod

from app.domain.value_objects.filter_config import FilterConfig


class FilterRepositoryPort(ABC):
    """Defineix el contracte que ha de complir qualsevol repositori de FilterConfig.

    Permet guardar i recuperar les configuracions de filtre definides per l'usuari.
    La infraestructura implementarà aquest port amb SQLAlchemy.
    """

    @abstractmethod
    def save(self, config: FilterConfig) -> None:
        """Persisteix una configuració de filtre a la base de dades.

        Args:
            config: FilterConfig a guardar.
        """

    @abstractmethod
    def get_active(self) -> FilterConfig:
        """Recupera la configuració de filtre activa.

        Returns:
            FilterConfig activa. Llança excepció si no n'hi ha cap.
        """

    @abstractmethod
    def list_all(self) -> list[FilterConfig]:
        """Recupera totes les configuracions de filtre guardades.

        Returns:
            Llista de FilterConfig (pot ser buida).
        """
