"""Tests for RetryManager — 2 retries with exponential backoff."""

from unittest.mock import AsyncMock, patch
import pytest

from app.infrastructure.services.retry_manager import RetryManager
from app.domain.exceptions.download_error import DownloadError


class TestRetryManagerSuccess:
    """Tests for successful execution paths."""

    @pytest.mark.asyncio
    async def test_returns_result_on_first_attempt(self):
        """Must return the result immediately when the operation succeeds."""
        manager = RetryManager(max_retries=2, backoff_base=0.0)
        operation = AsyncMock(return_value="ok")
        result = await manager.execute(operation)
        assert result == "ok"
        operation.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_result_on_second_attempt(self):
        """Must return the result after one failure and one success."""
        manager = RetryManager(max_retries=2, backoff_base=0.0)
        operation = AsyncMock(side_effect=[Exception("timeout"), "ok"])
        result = await manager.execute(operation)
        assert result == "ok"
        assert operation.call_count == 2

    @pytest.mark.asyncio
    async def test_returns_result_on_third_attempt(self):
        """Must return the result after two failures and one success."""
        manager = RetryManager(max_retries=2, backoff_base=0.0)
        operation = AsyncMock(
            side_effect=[Exception("err1"), Exception("err2"), "ok"])
        result = await manager.execute(operation)
        assert result == "ok"
        assert operation.call_count == 3


class TestRetryManagerFailure:
    """Tests for exhausted retries."""

    @pytest.mark.asyncio
    async def test_raises_download_error_after_all_retries_exhausted(self):
        """Must raise DownloadError when all attempts fail."""
        manager = RetryManager(max_retries=2, backoff_base=0.0)
        operation = AsyncMock(side_effect=Exception("always fails"))
        with pytest.raises(DownloadError):
            await manager.execute(operation)

    @pytest.mark.asyncio
    async def test_calls_operation_exactly_max_retries_plus_one_times(self):
        """With max_retries=2, must call the operation exactly 3 times total."""
        manager = RetryManager(max_retries=2, backoff_base=0.0)
        operation = AsyncMock(side_effect=Exception("fail"))
        with pytest.raises(DownloadError):
            await manager.execute(operation)
        assert operation.call_count == 3

    @pytest.mark.asyncio
    async def test_download_error_message_contains_original_reason(self):
        """DownloadError message must include the original exception message."""
        manager = RetryManager(max_retries=2, backoff_base=0.0)
        operation = AsyncMock(side_effect=Exception("connection refused"))
        with pytest.raises(DownloadError, match="connection refused"):
            await manager.execute(operation)


class TestRetryManagerBackoff:
    """Tests for backoff behaviour."""

    @pytest.mark.asyncio
    async def test_sleeps_between_retries(self):
        """Must call asyncio.sleep between retries."""
        manager = RetryManager(max_retries=2, backoff_base=1.0)
        operation = AsyncMock(
            side_effect=[Exception("err"), Exception("err"), "ok"])
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await manager.execute(operation)
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_backoff_is_exponential(self):
        """Sleep durations must grow exponentially (backoff_base * 2^attempt)."""
        manager = RetryManager(max_retries=2, backoff_base=1.0)
        operation = AsyncMock(
            side_effect=[Exception("e1"), Exception("e2"), "ok"])
        sleep_calls = []
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = lambda t: sleep_calls.append(t)
            await manager.execute(operation)
        assert sleep_calls[1] > sleep_calls[0]
