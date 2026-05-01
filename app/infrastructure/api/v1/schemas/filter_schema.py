"""Pydantic schema for filter configuration — API input/output validation."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.value_objects.filter_config import FilterConfig


class FilterSchema(BaseModel):
    """Request/response schema for the filter configuration endpoint."""

    tipus_expedient: int = Field(..., ge=0, description="Contract type (1 = licitació)")
    fase_vigent: int = Field(..., ge=0, description="Active phase filter (0 = open)")
    max_results: int = Field(20, ge=1, description="Max tenders to process per run")
    sector_keywords: list[str] = Field(default_factory=list, description="Sector keywords for post-filtering")
    min_pressupost: float = Field(0.0, ge=0.0, description="Minimum budget threshold")

    def to_domain(self) -> FilterConfig:
        """Convert to the FilterConfig domain value object."""
        return FilterConfig(
            tipus_expedient=self.tipus_expedient,
            fase_vigent=self.fase_vigent,
            max_results=self.max_results,
            sector_keywords=tuple(self.sector_keywords),
            min_pressupost=self.min_pressupost,
        )
