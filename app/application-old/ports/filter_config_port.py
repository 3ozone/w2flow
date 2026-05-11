"""Port (interface) for active filter configuration storage."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.value_objects.filter_config import FilterConfig


class FilterConfigPort(ABC):
    """Abstract contract for storing and retrieving the active FilterConfig."""

    @abstractmethod
    def get(self) -> FilterConfig | None:
        """Return the currently active FilterConfig, or None if not set."""

    @abstractmethod
    def save(self, fc: FilterConfig) -> None:
        """Persist the given FilterConfig as the active filter."""
