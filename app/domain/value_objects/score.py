"""Value object representing the scoring result for a tender (RN-03)."""
from dataclasses import dataclass, field

from app.domain.value_objects.traffic_light import TrafficLight


@dataclass(frozen=True)
class Score:
    """Scoring result for a single tender.

    Attributes:
        expedient_id: Identifier of the scored tender.
        total: Aggregated numeric score (0–100).
        detall: Breakdown by scoring criterion (criterion → points).

    Business rules (RN-03):
        - Viable if total >= 40.
        - Traffic light derived via :meth:`TrafficLight.from_score`.
    """

    expedient_id: str
    total: int
    detall: dict[str, int] = field(default_factory=dict)

    def is_viable(self) -> bool:
        """Return True when the score reaches the viability threshold (>=40)."""
        return self.total >= 40

    def assign_traffic_light(self) -> TrafficLight:
        """Return the traffic light colour that corresponds to this score."""
        return TrafficLight.from_score(self.total)
