"""Port (interface) for pipeline status storage."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dtos.pipeline_status_dto import PipelineStatusDTO


class PipelineStatusPort(ABC):
    """Abstract contract for reading and writing pipeline execution status."""

    @abstractmethod
    def get(self) -> PipelineStatusDTO:
        """Return the current pipeline status."""

    @abstractmethod
    def update(self, status: PipelineStatusDTO) -> None:
        """Persist a new pipeline status."""
