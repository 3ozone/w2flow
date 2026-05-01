"""RunPipelineCommand and its handler."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.application.ports.document_storage_port import DocumentStoragePort
from app.application.ports.licitacion_api_port import LicitationApiPort
from app.application.ports.tender_repository_port import TenderRepositoryPort
from app.application.use_cases.commands.download_documents_command import (
    DownloadDocumentsCommand,
    DownloadDocumentsCommandHandler,
)
from app.application.use_cases.commands.download_tenders_command import (
    DownloadTendersCommand,
    DownloadTendersCommandHandler,
)
from app.application.use_cases.commands.filter_tenders_command import (
    FilterTendersCommand,
    FilterTendersCommandHandler,
)
from app.application.use_cases.commands.score_tender_command import (
    ScoreTenderCommand,
    ScoreTenderCommandHandler,
)
from app.domain.entities.comparative_report import ComparativeReport
from app.domain.value_objects.filter_config import FilterConfig

log = logging.getLogger(__name__)


@dataclass
class RunPipelineCommand:
    """Command to execute the full download → filter → score → report pipeline."""

    filter_config: FilterConfig


class RunPipelineCommandHandler:
    """Orchestrates the full pipeline and returns a ComparativeReport.

    This handler belongs to the application layer and only depends on ports
    (abstractions). It never imports from the infrastructure or presentation layers.
    """

    def __init__(
        self,
        api: LicitationApiPort,
        repository: TenderRepositoryPort,
        storage: DocumentStoragePort,
    ) -> None:
        self._api = api
        self._repository = repository
        self._storage = storage

    async def handle(self, command: RunPipelineCommand) -> ComparativeReport:
        """Execute the pipeline and return the resulting ComparativeReport."""
        filter_config = command.filter_config

        # Stage 1: download from external API
        download_handler = DownloadTendersCommandHandler(
            api=self._api, repository=self._repository
        )
        tenders = await download_handler.handle(DownloadTendersCommand(filter_config))
        log.info("[PIPELINE] Downloaded %d tenders", len(tenders))

        # Stage 2: fine-grained filter
        filter_handler = FilterTendersCommandHandler()
        filtered = filter_handler.handle(
            FilterTendersCommand(tenders, filter_config))
        log.info("[PIPELINE] After filtering: %d tenders", len(filtered))

        # Stage 3: download documents for each tender
        doc_handler = DownloadDocumentsCommandHandler(
            api=self._api, storage=self._storage
        )
        scored_tenders = []
        for tender in filtered:
            documents = await doc_handler.handle(DownloadDocumentsCommand(tender))
            pdf_paths = [doc.file_path for doc in documents if doc.file_path]
            log.info(
                "[PIPELINE] Tender %s: %d documents downloaded",
                tender.expedient_id,
                len(documents),
            )

            # Stage 4: score each tender (pdf_texts populated in 6.4)
            score_handler = ScoreTenderCommandHandler(repository=self._repository)
            scored = await score_handler.handle(
                ScoreTenderCommand(
                    tender=tender,
                    filter_config=filter_config,
                    pdf_texts=[],
                )
            )
            scored_tenders.append(scored)
        log.info("[PIPELINE] Scored %d tenders", len(scored_tenders))

        # Stage 5: build and return the ComparativeReport
        return ComparativeReport(
            scored_tenders=scored_tenders,
            filter_config=filter_config,
        )
