"""FastAPI router for filter configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.infrastructure import dependencies
from app.infrastructure.api.v1.schemas.filter_schema import FilterSchema

router = APIRouter(tags=["filters"])


@router.get("/filters", response_model=FilterSchema | None)
async def get_filters() -> FilterSchema | None:
    """Return the currently active filter configuration."""
    fc = dependencies.filter_config_port.get()
    if fc is None:
        return None
    return FilterSchema.from_domain(fc)


@router.put("/filters", response_model=FilterSchema)
async def update_filters(payload: FilterSchema) -> FilterSchema:
    """Update and persist the active filter configuration."""
    dependencies.filter_config_port.save(payload.to_domain())
    return payload
