"""Value object representing the filter configuration for searching tenders on contractaciopublica.cat."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.exceptions.filter_validation_error import FilterValidationError


@dataclass(frozen=True)
class FilterConfig:
    """Search parameters sent to the contractaciopublica.cat API (RF-03, R-05).

    Coarse filtering is delegated to the API via :meth:`to_api_params`.
    Fine-grained filtering over the returned results is done via :meth:`matches`.

    Attributes:
        tipus_expedient: Contract type. ``1`` = licitacions/contractes.
        fase_vigent: Active phase filter. ``0`` = only open (anunci de licitació).
        max_results: Maximum number of tenders to process per run.
        sector_keywords: Additional sector keywords for post-API filtering.
        min_pressupost: Minimum budget threshold (0 = no limit).

    Raises:
        FilterValidationError: If any parameter value is out of range.
    """

    tipus_expedient: int
    fase_vigent: int
    max_results: int = 20
    sector_keywords: tuple[str, ...] = field(default_factory=tuple)
    min_pressupost: float = 0.0

    def __post_init__(self) -> None:
        if self.tipus_expedient < 0:
            raise FilterValidationError(
                f"tipus_expedient must be >= 0, got {self.tipus_expedient}"
            )
        if self.fase_vigent < 0:
            raise FilterValidationError(
                f"fase_vigent must be >= 0, got {self.fase_vigent}"
            )
        if self.max_results <= 0:
            raise FilterValidationError(
                f"max_results must be > 0, got {self.max_results}"
            )

    def to_api_params(self) -> dict:
        """Return the query parameters ready to send to ``/cerca-avancada``.

        Returns:
            A dict with ``tipusExpedient``, ``faseVigent``, ``size``, and ``page``.
        """
        return {
            "tipusExpedient": self.tipus_expedient,
            "faseVigent": self.fase_vigent,
            "size": self.max_results,
            "page": 0,
            "inclourePublicacionsPlacsp": "false",
            "sortField": "dataUltimaPublicacio",
            "sortOrder": "desc",
        }

    def matches(self, tender: dict) -> bool:
        """Return True if *tender* satisfies the additional filter criteria.

        Currently checks that ``tender["pressupost"]`` is not None and is
        greater than or equal to :attr:`min_pressupost`.

        Args:
            tender: A tender dict as returned by the API (must contain ``pressupost``).

        Returns:
            ``True`` if the tender passes all criteria, ``False`` otherwise.
        """
        pressupost = tender.get("pressupost")
        if pressupost is None:
            return self.min_pressupost == 0
        return float(pressupost) >= self.min_pressupost
