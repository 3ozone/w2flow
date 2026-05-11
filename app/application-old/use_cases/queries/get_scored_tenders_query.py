"""GetScoredTendersQuery and its handler."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.ports.tender_repository_port import TenderRepositoryPort
from app.domain.entities.scored_tender import ScoredTender


@dataclass
class GetScoredTendersQuery:
    """Query to retrieve a paginated list of scored tenders."""

    page: int = field(default=0)
    size: int = field(default=20)


class GetScoredTendersQueryHandler:
    """Returns a paginated list of ScoredTenders from the repository."""

    def __init__(self, repository: TenderRepositoryPort) -> None:
        self._repository = repository

    async def handle(self, query: GetScoredTendersQuery) -> list[ScoredTender]:
        """Delegate to the repository and return the results."""
        return await self._repository.list_scored(page=query.page, size=query.size)
