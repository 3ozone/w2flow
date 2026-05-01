"""FastAPI router for filter configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.infrastructure.api.v1.schemas.filter_schema import FilterSchema

router = APIRouter(tags=["filters"])

# Module-level active filter config — None until first PUT
_active_filter: FilterSchema | None = None


@router.get("/filters", response_model=FilterSchema | None)
async def get_filters() -> FilterSchema | None:
    """Return the currently active filter configuration."""
    return _active_filter


@router.put("/filters", response_model=FilterSchema)
async def update_filters(payload: FilterSchema) -> FilterSchema:
    """Update and persist the active filter configuration."""
    global _active_filter
    _active_filter = payload
    return _active_filter
