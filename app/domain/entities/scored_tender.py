"""Domain entity representing a tender together with its evaluation score (RF-06, RF-07)."""
from dataclasses import dataclass

from app.domain.entities.tender import Tender
from app.domain.value_objects.score import Score
from app.domain.value_objects.traffic_light import TrafficLight


@dataclass
class ScoredTender:
    """Una licitació ja avaluada, amb la seva puntuació de viabilitat.

    Agrega un :class:`Tender` i un :class:`Score` per oferir una vista
    unificada del resultat de l'avaluació, llesta per al panell comparatiu
    del Departament d'Estudis (RF-07).

    Attributes:
        tender: Dades de la licitació.
        score:  Puntuació calculada a partir de l'anàlisi NLP (RN-12).
    """

    tender: Tender
    score: Score

    def is_viable(self) -> bool:
        """Retorna True si la licitació supera el llindar de viabilitat (RN-03)."""
        return self.score.is_viable()

    def traffic_light(self) -> TrafficLight:
        """Retorna el semàfor de viabilitat corresponent a la puntuació (RN-03)."""
        return self.score.assign_traffic_light()
