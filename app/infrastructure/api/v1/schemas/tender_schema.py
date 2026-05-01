"""Pydantic schemas for scored tender API responses."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.domain.entities.scored_tender import ScoredTender


class ScoreSchema(BaseModel):
    """Score breakdown for a tender."""

    total: int
    traffic_light: str
    recomanacio: str
    detall: dict
    paraules_clau_trobades: list[str]
    penalitzacions: list[str]


class TenderSchema(BaseModel):
    """Response schema for a scored tender."""

    expedient_id: str
    publicacio_id: int
    titol: str
    organ: str
    pressupost: float
    codi_expedient: str
    fase: str
    data_publicacio: date
    is_go: bool
    score: ScoreSchema

    @classmethod
    def from_domain(cls, scored_tender: ScoredTender) -> "TenderSchema":
        """Build from a ScoredTender domain entity."""
        t = scored_tender.tender
        s = scored_tender.score
        return cls(
            expedient_id=t.expedient_id,
            publicacio_id=t.publicacio_id,
            titol=t.titol,
            organ=t.organ,
            pressupost=t.pressupost,
            codi_expedient=t.codi_expedient,
            fase=t.fase,
            data_publicacio=t.data_publicacio,
            is_go=scored_tender.is_go(),
            score=ScoreSchema(
                total=s.total,
                traffic_light=s.assign_traffic_light().value,
                recomanacio=s.recomanacio,
                detall=s.detall,
                paraules_clau_trobades=list(s.paraules_clau_trobades),
                penalitzacions=list(s.penalitzacions),
            ),
        )
