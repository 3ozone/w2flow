"""In-memory implementation of PipelineStatusPort."""
from __future__ import annotations

from app.application.dtos.pipeline_status_dto import PipelineStatusDTO
from app.application.ports.pipeline_status_port import PipelineStatusPort


class InMemoryPipelineStatusAdapter(PipelineStatusPort):
    """Stores pipeline status in memory (replaces _pipeline_status global)."""

    def __init__(self) -> None:
        self._status = PipelineStatusDTO()

    def get(self) -> PipelineStatusDTO:
        return self._status

    def update(self, status: PipelineStatusDTO) -> None:
        self._status = status
