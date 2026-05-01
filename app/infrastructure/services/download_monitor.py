"""Monitors download progress and records errors during pipeline execution."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DownloadMonitor:
    """Tracks progress and errors during a batch download run."""

    total: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[dict] = field(default_factory=list)

    def start(self, total: int) -> None:
        """Initialise a new run with the expected total number of items."""
        self.total = total
        self.downloaded = 0
        self.skipped = 0
        self.failed = 0
        self.errors = []
        logger.info("DownloadMonitor started — total=%d", total)

    def record_downloaded(self, expedient_id: str) -> None:
        """Mark one item as successfully downloaded."""
        self.downloaded += 1
        logger.debug("Downloaded %s (%d/%d)", expedient_id, self.downloaded, self.total)

    def record_skipped(self, expedient_id: str, reason: str) -> None:
        """Mark one item as skipped (e.g. duplicate or expired)."""
        self.skipped += 1
        logger.debug("Skipped %s — %s", expedient_id, reason)

    def record_error(self, expedient_id: str, error: Exception) -> None:
        """Record a failed download attempt."""
        self.failed += 1
        self.errors.append({"expedient_id": expedient_id, "error": str(error)})
        logger.warning("Error downloading %s: %s", expedient_id, error)

    def summary(self) -> dict:
        """Return a summary dict suitable for logging or API responses."""
        return {
            "total": self.total,
            "downloaded": self.downloaded,
            "skipped": self.skipped,
            "failed": self.failed,
            "errors": self.errors,
        }
