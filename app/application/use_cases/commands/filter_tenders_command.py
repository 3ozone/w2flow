"""FilterTendersCommand and its handler."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.tender import Tender
from app.domain.value_objects.filter_config import FilterConfig


@dataclass
class FilterTendersCommand:
    """Command to filter an in-memory list of tenders using a FilterConfig."""

    tenders: list[Tender]
    filter_config: FilterConfig


class FilterTendersCommandHandler:
    """Applies FilterConfig.matches() to a list of Tender entities."""

    def handle(self, command: FilterTendersCommand) -> list[Tender]:
        """Return only the tenders that satisfy the filter criteria."""
        return [
            tender
            for tender in command.tenders
            if command.filter_config.matches({"pressupost": tender.pressupost})
        ]
