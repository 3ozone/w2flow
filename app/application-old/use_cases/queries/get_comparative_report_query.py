"""GetComparativeReportQuery and its handler."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.ports.tender_repository_port import TenderRepositoryPort
from app.domain.entities.comparative_report import ComparativeReport
from app.domain.value_objects.filter_config import FilterConfig


@dataclass
class GetComparativeReportQuery:
    """Query to retrieve a comparative report of scored tenders."""

    filter_config: FilterConfig
    page: int = field(default=0)
    size: int = field(default=20)


class GetComparativeReportQueryHandler:
    """Builds a ComparativeReport from the persisted scored tenders."""

    def __init__(self, repository: TenderRepositoryPort) -> None:
        self._repository = repository

    async def handle(self, query: GetComparativeReportQuery) -> ComparativeReport:
        """Fetch scored tenders and wrap them in a ComparativeReport."""
        scored_tenders = await self._repository.list_scored(
            page=query.page, size=query.size
        )
        return ComparativeReport(
            scored_tenders=scored_tenders,
            filter_config=query.filter_config,
        )
