"""Domain entity representing the comparative report of evaluated tenders (RF-07)."""
from dataclasses import dataclass, field

from app.domain.entities.scored_tender import ScoredTender


@dataclass
class ComparativeReport:
    """Informe comparatiu de licitacions avaluades per al Departament d'Estudis.

    Conté la llista completa de licitacions puntuades i permet filtrar
    les viables perquè l'equip pugui prendre la decisió GO/NO GO (RF-07, RN-04).

    Attributes:
        tenders: Llista de licitacions amb la seva puntuació de viabilitat.
    """

    tenders: list[ScoredTender] = field(default_factory=list)

    def get_viable_tenders(self) -> list[ScoredTender]:
        """Retorna les licitacions que superen el llindar de viabilitat (RN-03)."""
        return [t for t in self.tenders if t.is_viable()]
