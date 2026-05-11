"""Pydantic schema for filter configuration — API input/output validation."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.value_objects.filter_config import FilterConfig


class FilterSchema(BaseModel):
    """Request/response schema for the filter configuration endpoint."""

    tipus_expedient: int = Field(..., ge=0,
                                 description="Contract type (1 = licitació)")
    fase_vigent: int = Field(..., ge=0,
                             description="Active phase filter (0 = open)")
    max_results: int = Field(
        20, ge=1, description="Max tenders to process per run")
    sector_keywords: list[str] = Field(
        default_factory=list, description="Sector keywords for post-filtering")
    min_pressupost: float = Field(
        0.0, ge=0.0, description="Minimum budget threshold")
    exclude_alerta_futura: bool = Field(
        True, description="Discard ALERTA_FUTURA tenders (no published budget yet)")
    cpv_codes: list[str] = Field(
        default_factory=list, description="CPV codes filter (empty = no filter, RN-07)")
    max_pressupost: float = Field(
        0.0, ge=0.0, description="Maximum budget (0 = no limit, RN-08)")

    def to_domain(self) -> FilterConfig:
        """Convert to the FilterConfig domain value object."""
        return FilterConfig(
            tipus_expedient=self.tipus_expedient,
            fase_vigent=self.fase_vigent,
            max_results=self.max_results,
            sector_keywords=tuple(self.sector_keywords),
            min_pressupost=self.min_pressupost,
            exclude_alerta_futura=self.exclude_alerta_futura,
            cpv_codes=tuple(self.cpv_codes),
            max_pressupost=self.max_pressupost,
        )

    @classmethod
    def from_domain(cls, fc: FilterConfig) -> FilterSchema:
        """Create a FilterSchema from a domain FilterConfig."""
        return cls(
            tipus_expedient=fc.tipus_expedient,
            fase_vigent=fc.fase_vigent,
            max_results=fc.max_results,
            sector_keywords=list(fc.sector_keywords),
            min_pressupost=fc.min_pressupost,
            exclude_alerta_futura=fc.exclude_alerta_futura,
            cpv_codes=list(fc.cpv_codes),
            max_pressupost=fc.max_pressupost,
        )
