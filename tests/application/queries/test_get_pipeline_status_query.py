"""Tests for GetPipelineStatusQueryHandler."""

from app.application.use_cases.queries.get_pipeline_status_query import (
    GetPipelineStatusQuery,
    GetPipelineStatusQueryHandler,
)
from app.infrastructure.repositories.in_memory_pipeline_status_adapter import (
    InMemoryPipelineStatusAdapter,
)
from app.application.dtos.pipeline_status_dto import PipelineStatusDTO, PipelineStateEnum


class TestGetPipelineStatusQueryHandler:
    """Tests for GetPipelineStatusQueryHandler."""

    def test_returns_idle_status_when_no_update_made(self):
        """handle() must return IDLE state before any update."""
        adapter = InMemoryPipelineStatusAdapter()
        handler = GetPipelineStatusQueryHandler(port=adapter)

        result = handler.handle(GetPipelineStatusQuery())

        assert result.state == PipelineStateEnum.IDLE

    def test_returns_updated_status_after_save(self):
        """handle() must return the last status saved via the port."""
        adapter = InMemoryPipelineStatusAdapter()
        handler = GetPipelineStatusQueryHandler(port=adapter)

        new_status = PipelineStatusDTO(
            state=PipelineStateEnum.RUNNING,
            total=10,
            downloaded=3,
        )
        adapter.update(new_status)

        result = handler.handle(GetPipelineStatusQuery())

        assert result.state == PipelineStateEnum.RUNNING
        assert result.total == 10
        assert result.downloaded == 3

    def test_returns_completed_status(self):
        """handle() must return COMPLETED when pipeline finishes."""
        adapter = InMemoryPipelineStatusAdapter()
        handler = GetPipelineStatusQueryHandler(port=adapter)

        adapter.update(PipelineStatusDTO(
            state=PipelineStateEnum.COMPLETED, total=5, downloaded=5))

        result = handler.handle(GetPipelineStatusQuery())

        assert result.state == PipelineStateEnum.COMPLETED

    def test_returns_failed_status_with_error(self):
        """handle() must return FAILED with error message when pipeline fails."""
        adapter = InMemoryPipelineStatusAdapter()
        handler = GetPipelineStatusQueryHandler(port=adapter)

        adapter.update(PipelineStatusDTO(
            state=PipelineStateEnum.FAILED,
            error="Connection timeout",
        ))

        result = handler.handle(GetPipelineStatusQuery())

        assert result.state == PipelineStateEnum.FAILED
        assert result.error == "Connection timeout"
