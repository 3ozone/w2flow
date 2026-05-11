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
        exclude_alerta_futura: If True, discard tenders in ALERTA_FUTURA phase.

    Raises:
        FilterValidationError: If any parameter value is out of range.
    """

    tipus_expedient: int
    fase_vigent: int
    max_results: int = 20
    sector_keywords: tuple[str, ...] = field(default_factory=tuple)
    min_pressupost: float = 0.0
    exclude_alerta_futura: bool = True
    cpv_codes: tuple[str, ...] = field(default_factory=tuple)
    max_pressupost: float = 0.0

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

        Checks:
        1. ``tender["pressupost"]`` >= :attr:`min_pressupost`.
        2. ``tender["titol"]`` does not contain any negative keyword (prefixed with ``-``).
           Positive keywords (no prefix) are used for scoring only — they do not exclude.

        Args:
            tender: A tender dict as returned by the API.

        Returns:
            ``True`` if the tender passes all criteria, ``False`` otherwise.
        """
        if self.exclude_alerta_futura and tender.get("fase") == "ALERTA_FUTURA":
            return False

        pressupost = tender.get("pressupost")
        if pressupost is None:
            if self.min_pressupost > 0:
                return False
        elif float(pressupost) < self.min_pressupost:
            return False

        if self.max_pressupost > 0 and pressupost is not None:
            if float(pressupost) > self.max_pressupost:
                return False

        if self.cpv_codes:
            codi_cpv = tender.get("codi_cpv")
            if codi_cpv not in self.cpv_codes:
                return False

        titol = (tender.get("titol") or "").lower()
        for kw in self.sector_keywords:
            if kw.startswith("-"):
                if kw[1:].lower() in titol:
                    return False

        return True
