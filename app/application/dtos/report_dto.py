"""DTO amb el resultat complet del pipeline per al panell (RF-06, RF-07)."""
from dataclasses import dataclass

from app.application.dtos.scored_tender_dto import ScoredTenderDTO


@dataclass(frozen=True)
class ReportDTO:
    """Resultat complet del pipeline: llista de licitacions puntuades i resum.

    No conté lògica de negoci. Serveix exclusivament per transferir dades
    des de la capa d'aplicació cap a la capa de presentació.

    Attributes:
        tenders:          Tupla de licitacions puntuades (totes, viables i no viables).
        total_candidates: Nombre total de licitacions candidates processades.
        total_viable:     Nombre de licitacions amb puntuació >= 40 (semàfor verd o groc).
    """

    tenders: tuple[ScoredTenderDTO, ...] = ()
    total_candidates: int = 0
    total_viable: int = 0
