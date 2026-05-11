"""GetActiveFilterQuery and its handler."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports.filter_config_port import FilterConfigPort
from app.domain.value_objects.filter_config import FilterConfig


@dataclass
class GetActiveFilterQuery:
    """Query to retrieve the currently active FilterConfig."""


class GetActiveFilterQueryHandler:
    """Returns the active FilterConfig via the FilterConfigPort."""

    def __init__(self, port: FilterConfigPort) -> None:
        self._port = port

    def handle(self, query: GetActiveFilterQuery) -> FilterConfig | None:
        """Return the active FilterConfig, or None if none has been saved."""
        return self._port.get()
