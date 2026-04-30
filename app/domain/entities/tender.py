"""Domain entity representing a public procurement tender."""
from dataclasses import dataclass
from datetime import date


@dataclass
class Tender:
    """Domain entity representing a public procurement tender."""

    expedient_id: str
    publicacio_id: int
    titol: str
    organ: str
    pressupost: float
    codi_expedient: str
    fase: str
    data_publicacio: date

    def __post_init__(self) -> None:
        if not self.expedient_id:
            raise ValueError("expedient_id cannot be empty")
        if not self.titol:
            raise ValueError("titol cannot be empty")
        if self.pressupost < 0:
            raise ValueError("pressupost cannot be negative")

    def is_new(self) -> bool:
        """Return True if the tender was published today."""
        return self.data_publicacio == date.today()

    def get_basic_info(self) -> dict:
        """Return a dict with the essential API fields."""
        return {
            "expedient_id": self.expedient_id,
            "publicacio_id": self.publicacio_id,
            "titol": self.titol,
            "organ": self.organ,
            "pressupost": self.pressupost,
            "codi_expedient": self.codi_expedient,
            "fase": self.fase,
            "data_publicacio": self.data_publicacio.isoformat(),
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tender):
            return NotImplemented
        return self.expedient_id == other.expedient_id

    def __hash__(self) -> int:
        return hash(self.expedient_id)
