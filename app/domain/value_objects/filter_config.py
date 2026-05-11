"""Value object representing the filter criteria configured by the user (RF-03, RN-14)."""
from dataclasses import dataclass

from app.domain.entities.tender import Tender
from app.domain.exceptions.invalid_filter_config_error import InvalidFilterConfigError


@dataclass(frozen=True)
class FilterConfig:
    """Criteri de cerca configurat per l'empresa per seleccionar licitacions.

    Camps obligatoris (filtres natius de l'API):
        tipus_expedient:       Tipus d'expedient (1 = licitacions i contractes).

    Camps opcionals natius (van a la query string de l'API si no són None):
        fase_vigent:             Fase vigent de la licitació. Per defecte 30
                                 (Anunci de licitació en termini). El catàleg de Dades Mestres
                                 usa IDs diferents (p.ex. 1000040) que NO funcionen en aquest
                                 endpoint. Valors vàlids: 0=Alerta futura, 30=Anunci licitació,
                                 40=En avaluació, 50=Adjudicació... (RN-14).
        ambit:                   Àmbit organitzatiu. Per defecte 1500001 (Generalitat).
        tipus_contracte:         Tipus de contracte. Per defecte 395 (Obres) (RN-14).
        procediment_adjudicacio: Procediment d'adjudicació. Per defecte 401 (Obert) (RN-14).

    Camps opcionals post-fetch (s'apliquen en memòria sobre els Tender descarregats):
        cpv_codes:          Conjunt de codis CPV permesos. Buit = sense filtre (RN-07).
        pressupost_maxim:   Pressupost màxim en EUR. 0.0 = sense límit (RN-08).
        nuts_codes:         Conjunt de codis NUTS permesos. Buit = sense filtre (RN-09).
        classifications:    Conjunt de grups empresarials permesos. Buit = sense filtre (RN-10).
        durada_minima_dies: Durada mínima en dies. 0 = sense límit inferior (RN-11).
        durada_maxima_dies: Durada màxima en dies. 0 = sense límit superior (RN-11).
        max_licitacions:    Nombre màxim de licitacions a processar per execució. Rang 1–100 (RN-13).
    """

    # Filtres natius obligatoris
    tipus_expedient: int

    # Filtres natius opcionals (amb valors per defecte correctes, RN-14)
    fase_vigent: int = 30
    ambit: int | None = 1500001
    tipus_contracte: int | None = 395
    procediment_adjudicacio: int | None = 401

    # Filtres post-fetch
    cpv_codes: tuple[str, ...] = ()
    pressupost_maxim: float = 0.0
    nuts_codes: tuple[str, ...] = ()
    classifications: tuple[str, ...] = ()
    durada_minima_dies: int = 0
    durada_maxima_dies: int = 0

    # Configuració del pipeline (RN-13)
    max_licitacions: int = 20

    def __post_init__(self) -> None:
        """Valida que max_licitacions estigui dins del rang permès [1, 100] (RN-13)."""
        if not 1 <= self.max_licitacions <= 100:
            raise InvalidFilterConfigError(
                field="max_licitacions",
                value=self.max_licitacions,
                min_value=1,
                max_value=100,
            )

    def to_api_params(self) -> dict:
        """Retorna els paràmetres de query string per a la crida /cerca-avancada.

        Els filtres opcionals només s'inclouen si tenen valor (no None).
        """
        params: dict = {
            "tipusExpedient": self.tipus_expedient,
            "faseVigent": self.fase_vigent,
            "page": 0,
            "size": self.max_licitacions,
            "inclourePublicacionsPlacsp": "false",
            "sortField": "dataUltimaPublicacio",
            "sortOrder": "desc",
        }
        if self.ambit is not None:
            params["ambit"] = self.ambit
        if self.tipus_contracte is not None:
            params["tipusContracte"] = self.tipus_contracte
        if self.procediment_adjudicacio is not None:
            params["procedimentAdjudicacio"] = self.procediment_adjudicacio
        return params

    def matches(self, tender: Tender) -> bool:
        """Retorna True si el tender compleix tots els filtres configurats.

        Aplica les regles RN-07, RN-08, RN-09, RN-10 i RN-11 en ordre.
        Si qualsevol filtre no es compleix, retorna False immediatament.
        """
        # RN-07: filtre CPV
        if self.cpv_codes and tender.cpv_principal not in self.cpv_codes:
            return False

        # RN-08: filtre pressupost màxim
        if self.pressupost_maxim > 0 and tender.pressupost is not None:
            if tender.pressupost > self.pressupost_maxim:
                return False

        # RN-09: filtre NUTS
        if self.nuts_codes and tender.nuts_code not in self.nuts_codes:
            return False

        # RN-10: filtre classificació empresarial
        if self.classifications:
            allowed = set(self.classifications)
            if not set(tender.classifications).issubset(allowed):
                return False

        # RN-11: filtre durada
        if tender.durada_dies is not None:
            if self.durada_minima_dies > 0 and tender.durada_dies < self.durada_minima_dies:
                return False
            if self.durada_maxima_dies > 0 and tender.durada_dies > self.durada_maxima_dies:
                return False

        return True
