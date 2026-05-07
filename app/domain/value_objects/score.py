"""Value object representing the score and recommendation for a tender's viability evaluation."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.value_objects.traffic_light import TrafficLight


@dataclass(frozen=True)
class Score:
    """Result of the viability evaluation of a tender (RF-06).

    Scoring scale: 0–70 points.

    * GREEN  (✅ RECOMANADA)  — total ≥ 50
    * YELLOW (⚠️ A VALORAR)  — total ≥ 25
    * RED    (❌ NO RECOMANADA) — total < 25

    Attributes:
        expedient_id: UUID of the evaluated tender.
        total: Numeric score (0–70).
        detall: Score breakdown by criterion
            (``pressupost``, ``sector_positiu``, ``sector_negatiu``,
            ``procediment_obert``, ``subcontractació``).
        paraules_clau_trobades: Positive-sector keywords found in the documents.
        penalitzacions: Negative-sector (IT/software) keywords found.
        recomanacio: Human-readable recommendation string.
    """

    expedient_id: str
    total: int
    detall: dict
    paraules_clau_trobades: tuple[str, ...] = field(default_factory=tuple)
    penalitzacions: tuple[str, ...] = field(default_factory=tuple)
    recomanacio: str = ""

    def assign_traffic_light(self) -> TrafficLight:
        """Return the traffic light colour based on :attr:`total`.

        Returns:
            :attr:`TrafficLight.GREEN` if total \u2265 70,
            :attr:`TrafficLight.YELLOW` if total \u2265 40,
            :attr:`TrafficLight.RED` otherwise.
        """
        return TrafficLight.from_score(self.total)

    def is_viable(self) -> bool:
        """Return True if the tender is worth reviewing (not RED).

        Returns:
            ``True`` when :attr:`total` \u2265 40 (YELLOW or GREEN, RN-03).
        """
        return self.total >= 40

    def to_report(self) -> dict:
        """Serialize the score for inclusion in the comparative report (RF-07).

        Returns:
            A dict with ``expedient_id``, ``total``, ``traffic_light``,
            ``recomanacio``, ``detall``, ``paraules_clau_trobades``,
            and ``penalitzacions``.
        """
        return {
            "expedient_id": self.expedient_id,
            "total": self.total,
            "traffic_light": self.assign_traffic_light().value,
            "recomanacio": self.recomanacio,
            "detall": self.detall,
            "paraules_clau_trobades": list(self.paraules_clau_trobades),
            "penalitzacions": list(self.penalitzacions),
        }
