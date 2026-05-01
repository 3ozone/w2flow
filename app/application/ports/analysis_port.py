"""Port (interface) for comparative analysis of scored tenders."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.scored_tender import ScoredTender


class AnalysisPort(ABC):
    """Abstract contract for generating a narrative comparative analysis."""

    @abstractmethod
    async def analyze(
        self,
        scored_tenders: list[ScoredTender],
        pdf_paths: list[str],
    ) -> str:
        """Return a narrative analysis text for the given scored tenders.

        Args:
            scored_tenders: List of scored tenders to analyse.
            pdf_paths: Paths to the downloaded PDF documents for context.

        Returns:
            A formatted narrative string with the comparative analysis.
        """
