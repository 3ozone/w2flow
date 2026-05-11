"""In-memory implementation of FilterConfigPort."""

from __future__ import annotations

from app.application.ports.filter_config_port import FilterConfigPort
from app.domain.value_objects.filter_config import FilterConfig


class InMemoryFilterConfigAdapter(FilterConfigPort):
    """Stores the active FilterConfig in process memory.

    Suitable for the current single-process deployment.
    Can be replaced by a DB-backed adapter without changing application code.
    """

    def __init__(self) -> None:
        self._filter: FilterConfig | None = None

    def get(self) -> FilterConfig | None:
        """Return the currently active FilterConfig, or None if not set."""
        return self._filter

    def save(self, fc: FilterConfig) -> None:
        """Persist the given FilterConfig as the active filter."""
        self._filter = fc
