"""Domain entity representing a scored tender, combining a Tender with its Score and Requirements."""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.tender import Tender
from app.domain.value_objects.requirements import Requirements
from app.domain.value_objects.score import Score


@dataclass
class ScoredTender:
    """Domain entity combining a Tender with its viability Score and Requirements."""

    tender: Tender
    score: Score
    requirements: Requirements | None

    def is_go(self) -> bool:
        """Return True if the tender is viable according to its score."""
        return self.score.is_viable()

    def get_summary(self) -> dict:
        """Return a concise summary combining tender info and score."""
        return {
            "expedient_id": self.tender.expedient_id,
            "titol": self.tender.titol,
            "organ": self.tender.organ,
            "pressupost": self.tender.pressupost,
            "total_score": self.score.total,
            "traffic_light": self.score.assign_traffic_light().value,
            "is_go": self.is_go(),
        }
