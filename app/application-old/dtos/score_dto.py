"""DTO for the Score value object — application layer serialization."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.value_objects.score import Score


@dataclass
class ScoreDTO:
    """Application-layer DTO for the Score value object."""

    expedient_id: str
    total: int
    detall: dict
    paraules_clau_trobades: list[str]
    penalitzacions: list[str]
    recomanacio: str

    @classmethod
    def from_domain(cls, score: Score) -> ScoreDTO:
        """Create a DTO from a domain Score value object."""
        return cls(
            expedient_id=score.expedient_id,
            total=score.total,
            detall=score.detall,
            paraules_clau_trobades=list(score.paraules_clau_trobades),
            penalitzacions=list(score.penalitzacions),
            recomanacio=score.recomanacio,
        )

    def to_domain(self) -> Score:
        """Convert this DTO back to a domain Score value object."""
        return Score(
            expedient_id=self.expedient_id,
            total=self.total,
            detall=self.detall,
            paraules_clau_trobades=tuple(self.paraules_clau_trobades),
            penalitzacions=tuple(self.penalitzacions),
            recomanacio=self.recomanacio,
        )
