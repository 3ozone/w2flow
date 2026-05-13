"""Use case que orquestra el pipeline complet de licitacions (RF-04, RF-05, RF-06, RF-07)."""
import json
import logging
from datetime import date, datetime, timezone

from app.application.dtos.report_dto import ReportDTO

logger = logging.getLogger(__name__)
from app.application.dtos.scored_tender_dto import ScoredTenderDTO
from app.application.ports.document_storage_port import DocumentStoragePort
from app.application.ports.nlp_analyser_port import NlpAnalyserPort
from app.application.ports.tender_api_port import TenderApiPort
from app.application.ports.tender_document_repository_port import TenderDocumentRepositoryPort
from app.application.ports.tender_repository_port import TenderRepositoryPort
from app.application.use_cases.fetch_candidates_use_case import FetchCandidatesUseCase
from app.domain.value_objects.filter_config import FilterConfig


class RunPipelineUseCase:
    """Orquestra el pipeline complet: fetch → documents → storage → NLP → score → ReportDTO.

    Responsabilitats:
    - Delegar la cerca i filtratge de candidats a FetchCandidatesUseCase.
    - Per cada candidat, obtenir els documents adjunts via TenderApiPort.
    - Descarregar i persistir en disc els documents obligatoris (PCAP, PPT, TECHNICAL_MEMORY).
    - Analitzar els PDFs amb NlpAnalyserPort per obtenir DocumentAnalysis.
    - Desar la puntuació i recomanació a la base de dades.
    - Construir un ScoredTenderDTO per cada licitació i empaquetarlo en un ReportDTO.

    Aquesta classe és la frontera pública de la capa d'aplicació cap a presentació.
    """

    def __init__(
        self,
        fetch_candidates: FetchCandidatesUseCase,
        api: TenderApiPort,
        nlp: NlpAnalyserPort,
        repository: TenderRepositoryPort,
        document_storage: DocumentStoragePort,
        document_repository: TenderDocumentRepositoryPort,
    ) -> None:
        """Inicialitza el use case amb les dependències injectades.

        Args:
            fetch_candidates:    Use case intern per obtenir licitacions candidates.
            api:                 Port per obtenir documents i descarregar PDFs.
            nlp:                 Port per analitzar PDFs amb NLP.
            repository:          Port per persistir les licitacions processades.
            document_storage:    Port per guardar PDFs en disc.
            document_repository: Port per guardar metadades de documents a la BD.
        """
        self._fetch_candidates = fetch_candidates
        self._api = api
        self._nlp = nlp
        self._repository = repository
        self._document_storage = document_storage
        self._document_repository = document_repository

    def execute(self, config: FilterConfig, today: date) -> ReportDTO:
        """Executa el pipeline complet i retorna el report amb les licitacions puntuades.

        Args:
            config: Configuració de filtres activa.
            today:  Data de referència per calcular licitacions expirades (RN-05).

        Returns:
            ReportDTO amb totes les licitacions puntuades i el resum de resultats.
        """
        candidates = self._fetch_candidates.execute(config=config, today=today)
        logger.info("[PIPELINE] %d candidats rebuts de FetchCandidatesUseCase", len(candidates))

        if not candidates:
            logger.warning("[PIPELINE] Cap candidat — el report queda buit")
            return ReportDTO()

        scored_dtos = []
        for tender in candidates:
            logger.info("[PIPELINE] Processant tender: expedient_id=%s", tender.expedient_id)
            documents, detail_fields = self._api.fetch_detail(tender.expedient_id, tender.publicacio_id)
            for field, value in detail_fields.items():
                setattr(tender, field, value)
            mandatory_docs = [doc for doc in documents if doc.is_mandatory()]
            logger.info(
                "[PIPELINE] tender=%s — %d documents totals, %d obligatoris",
                tender.expedient_id, len(documents), len(mandatory_docs),
            )
            pdf_bytes_list = [
                self._api.download_document(doc.doc_id, doc.hash) for doc in mandatory_docs
            ]

            # Persistir el tender PRIMER per satisfer la FK de tender_documents
            self._repository.save(tender)

            for doc, pdf_bytes in zip(mandatory_docs, pdf_bytes_list):
                tender_doc = self._document_storage.save(
                    expedient_id=tender.expedient_id,
                    filename=doc.titol,
                    content=pdf_bytes,
                )
                self._document_repository.save(tender_doc)

            filenames = [doc.titol for doc in mandatory_docs]
            analysis = self._nlp.analyse(
                expedient_id=tender.expedient_id,
                documents=pdf_bytes_list,
                filenames=filenames,
            )
            score = analysis.to_score()
            processed_at = datetime.now(tz=timezone.utc)

            for filename, comentari in analysis.comentaris_per_doc.items():
                self._document_repository.update_comentari(
                    expedient_id=tender.expedient_id,
                    filename=filename,
                    comentari=comentari,
                )

            logger.info(
                "[PIPELINE] tender=%s — score total=%s semàfor=%s",
                tender.expedient_id, score.total, score.assign_traffic_light().value,
            )

            traffic_light = score.assign_traffic_light().value
            recomendacio = analysis.recomendacio
            if recomendacio and traffic_light == "green" and (
                recomendacio.startswith("NO GO") or recomendacio.startswith("REVISAR")
            ):
                traffic_light = "yellow"

            self._repository.update_score(
                expedient_id=tender.expedient_id,
                score_total=score.total,
                score_traffic_light=traffic_light,
                score_detall=json.dumps(score.detall),
                recomendacio=recomendacio,
                created_at=processed_at,
            )

            scored_dtos.append(ScoredTenderDTO(
                expedient_id=tender.expedient_id,
                titol=tender.titol,
                organ=tender.organ,
                pressupost=tender.pressupost,
                total=score.total,
                traffic_light=traffic_light,
                detall=score.detall,
                recomendacio=recomendacio,
                created_at=processed_at,
            ))

        total_viable = sum(1 for dto in scored_dtos if dto.total >= 40)

        return ReportDTO(
            tenders=tuple(scored_dtos),
            total_candidates=len(scored_dtos),
            total_viable=total_viable,
        )
