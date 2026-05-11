"""Port (interface) for sending notifications."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.comparative_report import ComparativeReport


class NotificationPort(ABC):
    """Abstract contract for sending notifications (e.g. email) to users."""

    @abstractmethod
    async def send_report(self, report: ComparativeReport, recipient: str) -> None:
        """Send a comparative report to the given recipient."""

    @abstractmethod
    async def send_error(self, reason: str, recipient: str) -> None:
        """Send an error notification to the given recipient."""
