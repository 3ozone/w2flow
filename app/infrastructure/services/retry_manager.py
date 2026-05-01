"""RetryManager — executes async operations with exponential backoff retries."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from app.domain.exceptions.download_error import DownloadError


class RetryManager:
    """Executes an async operation with up to max_retries retries.

    On each failure waits backoff_base * 2^attempt seconds before retrying.
    Raises DownloadError if all attempts fail.
    """

    def __init__(self, max_retries: int = 2, backoff_base: float = 1.0) -> None:
        self._max_retries = max_retries
        self._backoff_base = backoff_base

    async def execute(self, operation: Callable[[], Awaitable[Any]]) -> Any:
        """Run operation, retrying on failure up to max_retries times."""
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                return await operation()
            except Exception as exc:
                last_error = exc
                if attempt < self._max_retries:
                    delay = self._backoff_base * (2 ** attempt)
                    await asyncio.sleep(delay)

        raise DownloadError(
            f"Operation failed after {self._max_retries + 1} attempts: {last_error}"
        )
