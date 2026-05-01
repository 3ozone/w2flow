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
from app.infrastructure.api.v1.routers import reports_router
from app.infrastructure.services.analysis_service import AnalysisService
from app.infrastructure.api.v1.routers import filters_router as filters_module
from app.infrastructure import dependencies
from app.infrastructure.api.v1.schemas.pipeline_status_schema import (
    PipelineState,
    PipelineStatusSchema,
)

log = logging.getLogger(__name__)

router = APIRouter(tags=["pipeline"])

# Module-level state — single in-process pipeline at a time
_pipeline_state: PipelineState = PipelineState.IDLE
_pipeline_status: PipelineStatusSchema = PipelineStatusSchema(
    state=PipelineState.IDLE)


def _build_dependencies() -> tuple[LicitationApiPort, TenderRepositoryPort]:
    """Return the shared API client and repository from the dependencies module."""
    if dependencies.repository is None:
        raise RuntimeError(
            "Repository not initialised — check DATABASE_URL in .env")
    return dependencies.api_client, dependencies.repository


async def _run_pipeline() -> None:
    """Execute the full pipeline via RunPipelineCommandHandler."""
    global _pipeline_state, _pipeline_status

    _pipeline_state = PipelineState.RUNNING
    _pipeline_status = PipelineStatusSchema(state=PipelineState.RUNNING)

    try:
        if filters_module._active_filter is None:
            raise RuntimeError(
                "No filter configured. Call PUT /api/v1/filters before running the pipeline."
            )

        filter_config = filters_module._active_filter.to_domain()
        log.info("[PIPELINE] Starting with filter: %s", filter_config)

        api, repository = _build_dependencies()
        storage = dependencies.document_storage

        handler = RunPipelineCommandHandler(
            api=api, repository=repository, storage=storage)
        report = await handler.handle(RunPipelineCommand(filter_config=filter_config))

        report_id = str(uuid.uuid4())
        reports_router.add_report(report_id, report)

        # Stage: narrative analysis via AnalysisService
        try:
            # pdf_paths: collect file_path from any Document entities stored during
            # the download stage. Currently document storage is not wired to
            # ScoredTender, so we pass an empty list — the agent will analyse
            # based on the tender metadata alone.
            pdf_paths: list[str] = []
            analysis_service = AnalysisService()
            analysis_text = await analysis_service.analyze(
                scored_tenders=report.scored_tenders,
                pdf_paths=pdf_paths,
            )
            reports_router.add_analysis(report_id, analysis_text)
        except Exception as exc:
            log.warning("[PIPELINE] Analysis failed (non-fatal): %s", exc)

        total = len(report.scored_tenders)
        log.info(
            "[PIPELINE] Completed. Scored %d tenders. Report id: %s", total, report_id)
        _pipeline_state = PipelineState.COMPLETED
        _pipeline_status = PipelineStatusSchema(
            state=PipelineState.COMPLETED,
            total=total,
            downloaded=total,
        )

    except Exception as exc:
        log.exception("[PIPELINE] Failed: %s", exc)
        _pipeline_state = PipelineState.FAILED
        _pipeline_status = PipelineStatusSchema(
            state=PipelineState.FAILED, error=str(exc)
        )


@router.post("/pipeline/run", status_code=202, response_model=PipelineStatusSchema)
async def run_pipeline(background_tasks: BackgroundTasks) -> PipelineStatusSchema:
    """Launch the pipeline in the background.

    Returns 409 if a pipeline is already running.
    """
    global _pipeline_state, _pipeline_status

    if _pipeline_state == PipelineState.RUNNING:
        raise HTTPException(status_code=409, detail="Pipeline already running")

    background_tasks.add_task(_run_pipeline)
    _pipeline_status = PipelineStatusSchema(state=PipelineState.RUNNING)
    return _pipeline_status


@router.get("/pipeline/status", response_model=PipelineStatusSchema)
async def get_pipeline_status() -> PipelineStatusSchema:
    """Return the current pipeline state and progress counters."""
    return _pipeline_status
