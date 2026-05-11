"""Application-layer DTO for pipeline execution status."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PipelineStateEnum(str, Enum):
    """Enum for pipeline execution states."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineStatusDTO:
    """Carries the current pipeline execution state across layers."""

    state: PipelineStateEnum = PipelineStateEnum.IDLE
    total: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    error: str | None = None
