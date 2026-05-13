"""Use case per obtenir les licitacions candidates a analitzar (RF-02, RF-03, RN-01, RN-05, RN-06)."""
import logging
from datetime import date

from app.application.ports.tender_api_port import TenderApiPort

logger = logging.getLogger(__name__)
from app.application.ports.tender_repository_port import TenderRepositoryPort
from app.domain.entities.tender import Tender
from app.domain.value_objects.filter_config import FilterConfig


class FetchCandidatesUseCase:
    """Obté les licitacions candidates aplicant filtres natius, post-fetch i deduplicació.

    Responsabilitats:
    - Cridar l'API amb els paràmetres natius de FilterConfig.
    - Descartar licitacions que no passen el filtre post-fetch (FilterConfig.matches).
    - Descartar licitacions expirades (Tender.is_expired).
    - Descartar licitacions ja processades a la BD (TenderRepositoryPort.is_duplicate).

    Aquesta classe és interna: només la consumeix RunPipelineUseCase.
    """

    def __init__(self, api: TenderApiPort, repository: TenderRepositoryPort) -> None:
        """Inicialitza el use case amb les dependències injectades.

        Args:
            api:        Port per accedir a l'API externa de contractació pública.
            repository: Port per comprovar duplicats a la base de dades.
        """
        self._api = api
        self._repository = repository

    def execute(self, config: FilterConfig, today: date) -> list[Tender]:
        """Executa el cas d'ús i retorna la llista de licitacions candidates.

        Comença a la pàgina count//max_licitacions per saltar les ja processades,
        i pagina endavant fins acumular max_licitacions candidates noves o fins
        que l'API no retorni més resultats.

        Args:
            config: Configuració de filtres activa.
            today:  Data de referència per calcular licitacions expirades (RN-05).

        Returns:
            Llista de Tender que han passat tots els filtres i no són duplicats.
        """
        max_licitacions = config.max_licitacions
        existing_count = self._repository.count()
        page = existing_count // max_licitacions if max_licitacions > 0 else 0

        candidates: list[Tender] = []

        while len(candidates) < max_licitacions:
            params = {**config.to_api_params(), "page": page}
            tenders = self._api.fetch_tenders(params)
            logger.info("[FETCH] Pàgina %d — rebuts %d tenders de l'API", page, len(tenders))

            if not tenders:
                break

            for tender in tenders:
                if not config.matches(tender):
                    logger.debug(
                        "[FETCH] Descartat (no passa matches): expedient_id=%s",
                        tender.expedient_id,
                    )
                    continue
                if tender.is_expired(today):
                    logger.debug(
                        "[FETCH] Descartat (expirat data_limit=%s): expedient_id=%s",
                        tender.data_limit, tender.expedient_id,
                    )
                    continue
                if self._repository.is_duplicate(tender.expedient_id):
                    logger.debug(
                        "[FETCH] Descartat (duplicat a BD): expedient_id=%s",
                        tender.expedient_id,
                    )
                    continue
                logger.debug("[FETCH] Candidat acceptat: expedient_id=%s", tender.expedient_id)
                candidates.append(tender)
                if len(candidates) >= max_licitacions:
                    break

            # Si l'API retorna menys resultats que la mida de pàgina, ja no hi ha més pàgines
            if len(tenders) < max_licitacions:
                break

            page += 1

        logger.info("[FETCH] %d candidats finals", len(candidates))
        return candidates
