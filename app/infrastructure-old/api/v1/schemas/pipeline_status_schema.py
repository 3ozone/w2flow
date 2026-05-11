"""Pydantic schemas for pipeline status API responses."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class PipelineState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStatusSchema(BaseModel):
    """Response schema for pipeline status and progress."""

    state: PipelineState
    total: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    error: str | None = None
