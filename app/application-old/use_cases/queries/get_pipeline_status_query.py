"""Query and handler for retrieving the current pipeline status."""
from __future__ import annotations

from dataclasses import dataclass

from app.application.dtos.pipeline_status_dto import PipelineStatusDTO
from app.application.ports.pipeline_status_port import PipelineStatusPort


@dataclass
class GetPipelineStatusQuery:
    """Query to retrieve the current pipeline execution status."""


class GetPipelineStatusQueryHandler:
    """Returns the current pipeline status via PipelineStatusPort."""

    def __init__(self, port: PipelineStatusPort) -> None:
        self._port = port

    def handle(self, query: GetPipelineStatusQuery) -> PipelineStatusDTO:
        """Return the current pipeline status."""
        return self._port.get()
