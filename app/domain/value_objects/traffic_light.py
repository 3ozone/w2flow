"""Value object representing the viability signal (traffic light) for a scored tender."""
from enum import Enum


class TrafficLight(Enum):
    """Viability signal for a scored tender.

    Thresholds (based on a 70-point scoring scale):

    * GREEN  — total ≥ 50  → recommended
    * YELLOW — total ≥ 25  → worth reviewing
    * RED    — total < 25  → not recommended
    """

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

    @classmethod
    def from_score(cls, total: int) -> "TrafficLight":
        """Return the traffic light colour for a given score total.

        Args:
            total: The numeric score (0–70).

        Returns:
            :attr:`GREEN` if *total* ≥ 50,
            :attr:`YELLOW` if *total* ≥ 25,
            :attr:`RED` otherwise.
        """
        if total >= 50:
            return cls.GREEN
        if total >= 25:
            return cls.YELLOW
        return cls.RED
