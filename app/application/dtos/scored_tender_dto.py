"""DTO amb les dades aplanades d'una licitació puntuada per al panell (RF-06, RF-07)."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoredTenderDTO:
    """Dades aplanades d'una licitació puntuada per mostrar al panell.

    No conté lògica de negoci. Serveix exclusivament per transferir dades
    des de la capa d'aplicació cap a la capa de presentació.

    Attributes:
        expedient_id:  Identificador únic de l'expedient.
        titol:         Títol de la licitació.
        organ:         Nom de l'òrgan de contractació.
        pressupost:    Pressupost base sense IVA en EUR (None si no disponible).
        total:         Puntuació total NLP (0-100).
        traffic_light: Semàfor de viabilitat: "green", "yellow" o "red".
        detall:        Desglose de puntuació per criteri (RN-12).
    """

    expedient_id: str
    titol: str
    organ: str
    pressupost: float | None
    total: int
    traffic_light: str
    detall: dict[str, int] = field(default_factory=dict)
