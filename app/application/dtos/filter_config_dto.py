"""Data Transfer Object for FilterConfig, used in the application layer."""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.value_objects.filter_config import FilterConfig


@dataclass
class FilterConfigDTO:
    """Application-layer DTO for FilterConfig."""

    tipus_expedient: int
    fase_vigent: int
    max_results: int
    sector_keywords: list[str]
    min_pressupost: float

    @classmethod
    def from_domain(cls, fc: FilterConfig) -> FilterConfigDTO:
        """Create a DTO from a domain FilterConfig."""
        return cls(
            tipus_expedient=fc.tipus_expedient,
            fase_vigent=fc.fase_vigent,
            max_results=fc.max_results,
            sector_keywords=list(fc.sector_keywords),
            min_pressupost=fc.min_pressupost,
        )

    def to_domain(self) -> FilterConfig:
        """Convert this DTO back to a domain FilterConfig."""
        return FilterConfig(
            tipus_expedient=self.tipus_expedient,
            fase_vigent=self.fase_vigent,
            max_results=self.max_results,
            sector_keywords=tuple(self.sector_keywords),
            min_pressupost=self.min_pressupost,
        )
