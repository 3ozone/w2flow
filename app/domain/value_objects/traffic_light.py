"""Value object representing the viability signal for a scored tender (RN-03)."""
from enum import Enum


class TrafficLight(Enum):
    """Viability signal based on a numeric score.

    Thresholds (RN-03):
    - GREEN  >= 70 — recommended
    - YELLOW >= 40 — worth reviewing
    - RED    <  40 — not recommended
    """

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

    @classmethod
    def from_score(cls, total: int) -> "TrafficLight":
        """Return the traffic light colour for a given score."""
        if total >= 70:
            return cls.GREEN
        if total >= 40:
            return cls.YELLOW
        return cls.RED
