"""FastAPI router for pipeline execution and status endpoints."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.application.ports.licitacion_api_port import LicitationApiPort
from app.application.ports.tender_repository_port import TenderRepositoryPort
from app.application.use_cases.commands.run_pipeline_command import (
    RunPipelineCommand,
    RunPipelineCommandHandler,
)
from app.application.dtos.pipeline_status_dto import PipelineStateEnum, PipelineStatusDTO
from app.infrastructure.api.v1.routers import reports_router
from app.infrastructure.services.analysis_service import AnalysisService
from app.infrastructure.services.pdf_text_extractor import PdfTextExtractor
from app.infrastructure import dependencies
from app.infrastructure.api.v1.schemas.pipeline_status_schema import (
    PipelineState,
    PipelineStatusSchema,
)

log = logging.getLogger(__name__)

router = APIRouter(tags=["pipeline"])


def _dto_to_schema(dto: PipelineStatusDTO) -> PipelineStatusSchema:
    """Convert application DTO to infrastructure Pydantic schema."""
    return PipelineStatusSchema(
        state=PipelineState(dto.state.value),
        total=dto.total,
        downloaded=dto.downloaded,
        skipped=dto.skipped,
        failed=dto.failed,
        error=dto.error,
    )


def _build_dependencies() -> tuple[LicitationApiPort, TenderRepositoryPort]:
    """Return the shared API client and repository from the dependencies module."""
    if dependencies.repository is None:
        raise RuntimeError(
            "Repository not initialised — check DATABASE_URL in .env")
    return dependencies.api_client, dependencies.repository


async def _run_pipeline() -> None:
    """Execute the full pipeline via RunPipelineCommandHandler."""
    dependencies.pipeline_status_port.update(
        PipelineStatusDTO(state=PipelineStateEnum.RUNNING)
    )

    try:
        filter_config = dependencies.filter_config_port.get()
        if filter_config is None:
            raise RuntimeError(
                "No filter configured. Call PUT /api/v1/filters before running the pipeline."
            )

        log.info("[PIPELINE] Starting with filter: %s", filter_config)

        api, repository = _build_dependencies()
        storage = dependencies.document_storage

        handler = RunPipelineCommandHandler(
            api=api, repository=repository, storage=storage,
            pdf_extractor=PdfTextExtractor(),
        )
        report = await handler.handle(RunPipelineCommand(filter_config=filter_config))

        report_id = str(uuid.uuid4())
        reports_router.add_report(report_id, report)

        # Stage: narrative analysis via AnalysisService
        try:
            all_pdf_paths: list[str] = []
            if storage:
                for st in report.scored_tenders:
                    docs = await storage.list_documents(st.tender.expedient_id)
                    all_pdf_paths.extend(d.file_path for d in docs if d.file_path)
            analysis_service = AnalysisService()
            analysis_text = await analysis_service.analyze(
                scored_tenders=report.scored_tenders,
                pdf_paths=all_pdf_paths,
            )
            reports_router.add_analysis(report_id, analysis_text)
        except Exception as exc:
            log.warning("[PIPELINE] Analysis failed (non-fatal): %s", exc)

        total = len(report.scored_tenders)
        log.info(
            "[PIPELINE] Completed. Scored %d tenders. Report id: %s", total, report_id)
        dependencies.pipeline_status_port.update(PipelineStatusDTO(
            state=PipelineStateEnum.COMPLETED,
            total=total,
            downloaded=total,
        ))

    except Exception as exc:
        log.exception("[PIPELINE] Failed: %s", exc)
        dependencies.pipeline_status_port.update(PipelineStatusDTO(
            state=PipelineStateEnum.FAILED, error=str(exc)
        ))


@router.post("/pipeline/run", status_code=202, response_model=PipelineStatusSchema)
async def run_pipeline(background_tasks: BackgroundTasks) -> PipelineStatusSchema:
    """Launch the pipeline in the background.

    Returns 409 if a pipeline is already running.
    """
    current = dependencies.pipeline_status_port.get()
    if current.state == PipelineStateEnum.RUNNING:
        raise HTTPException(status_code=409, detail="Pipeline already running")

    background_tasks.add_task(_run_pipeline)
    running_dto = PipelineStatusDTO(state=PipelineStateEnum.RUNNING)
    dependencies.pipeline_status_port.update(running_dto)
    return _dto_to_schema(running_dto)


@router.get("/pipeline/status", response_model=PipelineStatusSchema)
async def get_pipeline_status() -> PipelineStatusSchema:
    """Return the current pipeline state and progress counters."""
    return _dto_to_schema(dependencies.pipeline_status_port.get())
