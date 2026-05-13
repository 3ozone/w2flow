"""Domain entity representing a tender fetched from contractaciopublica.cat (RF-02)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Tender:
    """A public tender published on the PSCP platform.

    Fields are populated in two steps:
      1. Summary fields from ``/cerca-avancada`` (expedient_id, publicacio_id, organ, titol).
      2. Detail fields from ``/detall-publicacio-expedient`` (all others).

    Attributes:
        expedient_id: UUID of the expedient — primary identifier (never null).
        publicacio_id: Numeric publication ID — needed to fetch the detail.
        organ: Name of the contracting body.
        titol: Title of the tender.
        codi_expedient: Internal code assigned by the contracting body (nullable).
        pressupost: Base budget without VAT in EUR (nullable).
        cpv_principal: Main CPV code, e.g. ``"45000000-7"`` (nullable).
        data_limit: Deadline for submitting offers (nullable, timezone-aware).
        durada_dies: Estimated duration in days (nullable).
        tipus_contracte_id: Contract type ID from the API (nullable).
        procediment_id: Procurement procedure ID from the API (nullable).
        nuts_code: NUTS code for the place of execution, e.g. ``"ES512"`` (nullable).
        classifications: Tuple of required business classification groups, e.g. ``("C", "G")``.
    """

    # --- Identification (from /cerca-avancada) ---
    expedient_id: str
    publicacio_id: int
    organ: str
    titol: str

    # --- Detail fields (from /detall-publicacio-expedient) ---
    codi_expedient: str | None = None
    pressupost: float | None = None
    cpv_principal: str | None = None
    data_limit: datetime | None = None
    durada_dies: int | None = None

    # --- Filter fields (RF-03 / RN-09 / RN-10) ---
    tipus_contracte_id: int | None = None
    procediment_id: int | None = None
    nuts_code: str | None = None
    classifications: tuple[str, ...] = field(default_factory=tuple)

    def is_expired(self, today: date) -> bool:
        """Return True if the submission deadline has already passed (RN-05).

        Args:
            today: The reference date to compare against (typically ``date.today()``).

        Returns:
            ``True`` when :attr:`data_limit` is set and its date is strictly
            before *today*. ``False`` when there is no deadline or the deadline
            is today or in the future.
        """
        if self.data_limit is None:
            return False
        return self.data_limit.date() < today
