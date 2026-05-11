"""Domain entity representing the NLP analysis result of a tender document (RF-05, RN-12)."""
from dataclasses import dataclass

from app.domain.exceptions.invalid_score_error import InvalidScoreError
from app.domain.value_objects.score import Score

_LIMITS = {
    "solvencia": 30,
    "criteris_adjudicacio": 25,
    "clausules_atipiques": 20,
    "procediment": 15,
    "condicions_execucio": 10,
}


@dataclass
class DocumentAnalysis:
    """Resultat de l'anàlisi NLP dels documents obligatoris d'una licitació (PCAP/PPT).

    Cada camp conté la puntuació parcial assignada per l'agent Timbal
    per a cadascun dels criteris definits a RN-12.

    Attributes:
        expedient_id:          UUID de la licitació analitzada.
        solvencia:             Puntuació de solvència assolible (0–30).
        criteris_adjudicacio:  Puntuació per criteris d'adjudicació favorables (0–25).
        clausules_atipiques:   Puntuació per absència de clàusules atípiques (0–20).
        procediment:           Puntuació pel tipus de procediment d'accés (0–15).
        condicions_execucio:   Puntuació per condicions d'execució (0–10).
    """

    expedient_id: str
    solvencia: int
    criteris_adjudicacio: int
    clausules_atipiques: int
    procediment: int
    condicions_execucio: int

    def __post_init__(self) -> None:
        """Valida que cada criteri estigui dins del rang vàlid (RN-12)."""
        for field, max_value in _LIMITS.items():
            value = getattr(self, field)
            if value < 0 or value > max_value:
                raise InvalidScoreError(field=field, value=value, max_value=max_value)

    def to_score(self) -> Score:
        """Suma els 5 criteris i retorna un Score per a la licitació (RN-12)."""
        total = (
            self.solvencia
            + self.criteris_adjudicacio
            + self.clausules_atipiques
            + self.procediment
            + self.condicions_execucio
        )
        detall = {
            "solvencia": self.solvencia,
            "criteris_adjudicacio": self.criteris_adjudicacio,
            "clausules_atipiques": self.clausules_atipiques,
            "procediment": self.procediment,
            "condicions_execucio": self.condicions_execucio,
        }
        return Score(expedient_id=self.expedient_id, total=total, detall=detall)
