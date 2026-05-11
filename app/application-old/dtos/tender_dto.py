"""Data Transfer Object for Tender, used in the application layer."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.entities.tender import Tender


@dataclass
class TenderDTO:
    """Application-layer DTO for the Tender entity."""

    expedient_id: str
    publicacio_id: int
    titol: str
    organ: str
    pressupost: float
    codi_expedient: str
    fase: str
    data_publicacio: str  # ISO 8601 string

    @classmethod
    def from_domain(cls, tender: Tender) -> TenderDTO:
        """Create a DTO from a domain Tender entity."""
        return cls(
            expedient_id=tender.expedient_id,
            publicacio_id=tender.publicacio_id,
            titol=tender.titol,
            organ=tender.organ,
            pressupost=tender.pressupost,
            codi_expedient=tender.codi_expedient,
            fase=tender.fase,
            data_publicacio=tender.data_publicacio.isoformat(),
        )

    def to_domain(self) -> Tender:
        """Convert this DTO back to a domain Tender entity."""
        return Tender(
            expedient_id=self.expedient_id,
            publicacio_id=self.publicacio_id,
            titol=self.titol,
            organ=self.organ,
            pressupost=self.pressupost,
            codi_expedient=self.codi_expedient,
            fase=self.fase,
            data_publicacio=date.fromisoformat(self.data_publicacio),
        )
