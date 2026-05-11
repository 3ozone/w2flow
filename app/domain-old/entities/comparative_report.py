"""Domain entity representing a comparative report of scored tenders."""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.scored_tender import ScoredTender
from app.domain.value_objects.filter_config import FilterConfig


@dataclass
class ComparativeReport:
    """Domain entity aggregating scored tenders from a single search run."""

    scored_tenders: list[ScoredTender]
    filter_config: FilterConfig

    def get_viable_tenders(self) -> list[ScoredTender]:
        """Return only the tenders where is_go() is True."""
        return [st for st in self.scored_tenders if st.is_go()]

    def generate_json(self) -> dict:
        """Return a fully serializable report."""
        return {
            "total_count": len(self.scored_tenders),
            "viable_count": len(self.get_viable_tenders()),
            "tenders": [st.get_summary() for st in self.scored_tenders],
            "filter_config": self.filter_config.to_api_params(),
        }
