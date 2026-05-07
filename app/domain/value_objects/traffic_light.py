"""Value object representing the viability signal (traffic light) for a scored tender."""
from enum import Enum


class TrafficLight(Enum):
    """Viability signal for a scored tender.

    Thresholds (RN-03, 100-point scoring scale):

    * GREEN  — total ≥ 70  → recommended
    * YELLOW — total ≥ 40  → worth reviewing
    * RED    — total < 40  → not recommended
    """

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

    @classmethod
    def from_score(cls, total: int) -> "TrafficLight":
        """Return the traffic light colour for a given score total.

        Args:
            total: The numeric score (0–100).

        Returns:
            :attr:`GREEN` if *total* ≥ 70,
            :attr:`YELLOW` if *total* ≥ 40,
            :attr:`RED` otherwise.
        """
        if total >= 70:
            return cls.GREEN
        if total >= 40:
            return cls.YELLOW
        return cls.RED
