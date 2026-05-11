"""Data Transfer Object for FilterConfig, used in the application layer."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.value_objects.filter_config import FilterConfig


@dataclass
class FilterConfigDTO:
    """Application-layer DTO for FilterConfig."""

    tipus_expedient: int
    fase_vigent: int
    max_results: int
    sector_keywords: list[str]
    min_pressupost: float
    exclude_alerta_futura: bool = True
    cpv_codes: list[str] = field(default_factory=list)
    max_pressupost: float = 0.0

    @classmethod
    def from_domain(cls, fc: FilterConfig) -> FilterConfigDTO:
        """Create a DTO from a domain FilterConfig."""
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

    def to_domain(self) -> FilterConfig:
        """Convert this DTO back to a domain FilterConfig."""
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
    def from_domain(cls, fc: FilterConfig) -> FilterConfigDTO:
        """Create a DTO from a domain FilterConfig."""
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

    def to_domain(self) -> FilterConfig:
        """Convert this DTO back to a domain FilterConfig."""
        return FilterConfig(
            tipus_expedient=self.tipus_expedient,
            fase_vigent=self.fase_vigent,
            max_results=self.max_results,
            sector_keywords=tuple(self.sector_keywords),
            min_pressupost=self.min_pressupost,
            exclude_alerta_futura=self.exclude_alerta_futura,
            cpv_codes=tuple(self.cpv_codes or []),
            max_pressupost=self.max_pressupost,
        )
