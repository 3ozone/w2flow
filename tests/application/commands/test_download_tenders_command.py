"""Tests for DownloadTendersCommandHandler."""

from unittest.mock import AsyncMock
from datetime import date
import pytest

from app.application.use_cases.commands.download_tenders_command import (
    DownloadTendersCommand,
    DownloadTendersCommandHandler,
)
from app.domain.exceptions.download_error import DownloadError
from app.domain.entities.tender import Tender
from app.domain.value_objects.filter_config import FilterConfig


def _make_filter_config(**kwargs) -> FilterConfig:
    defaults = {
        "tipus_expedient": 1,
        "fase_vigent": 0,
        "sector_keywords": ("construcció", "obra"),
        "min_pressupost": 0.0,
    }
    defaults.update(kwargs)
    return FilterConfig(**defaults)


def _make_api_tender(expedient_id: str = "uuid-1", pressupost: float = 100_000.0) -> dict:
    """Return a raw API dict matching the contractaciopublica.cat response shape."""
    return {
        "expedientId": expedient_id,
        "id": 42,
        "titol": f"Licitació {expedient_id}",
        "organ": "Ajuntament de Barcelona",
        "pressupostLicitacio": pressupost,
        "codiExpedient": f"EXP-{expedient_id}",
        "fase": "0",
        "dataPublicacio": date.today().isoformat(),
    }


class TestDownloadTendersCommandHandler:
    """Tests for DownloadTendersCommandHandler."""

    def _make_handler(self, api_return=None, repo_save=None):
        api = AsyncMock()
        api.fetch_page.return_value = api_return if api_return is not None else []
        repository = AsyncMock()
        return DownloadTendersCommandHandler(api=api, repository=repository), api, repository

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_returns_list_of_tenders(self):
        """handle() must return a list of Tender instances."""
        handler, _, _ = self._make_handler(api_return=[_make_api_tender()])
        command = DownloadTendersCommand(filter_config=_make_filter_config())
        result = await handler.handle(command)
        assert len(result) == 1
        assert isinstance(result[0], Tender)

    @pytest.mark.asyncio
    async def test_saves_each_tender_to_repository(self):
        """handle() must call repository.save() for each downloaded tender."""
        handler, _, repository = self._make_handler(
            api_return=[_make_api_tender("uuid-1"), _make_api_tender("uuid-2")]
        )
        command = DownloadTendersCommand(filter_config=_make_filter_config())
        await handler.handle(command)
        assert repository.save.call_count == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_api_returns_no_tenders(self):
        """handle() must return empty list when the API page is empty."""
        handler, _, _ = self._make_handler(api_return=[])
        command = DownloadTendersCommand(filter_config=_make_filter_config())
        result = await handler.handle(command)
        assert result == []

    @pytest.mark.asyncio
    async def test_passes_filter_config_to_api(self):
        """handle() must pass the FilterConfig to api.fetch_page()."""
        handler, api, _ = self._make_handler(api_return=[])
        fc = _make_filter_config()
        command = DownloadTendersCommand(filter_config=fc)
        await handler.handle(command)
        api.fetch_page.assert_called_once_with(fc, 0)

    @pytest.mark.asyncio
    async def test_filters_tenders_below_min_pressupost(self):
        """handle() must exclude tenders below filter_config.min_pressupost."""
        handler, _, _ = self._make_handler(api_return=[
            _make_api_tender("uuid-high", pressupost=200_000.0),
            _make_api_tender("uuid-low", pressupost=5_000.0),
        ])
        command = DownloadTendersCommand(
            filter_config=_make_filter_config(min_pressupost=50_000.0)
        )
        result = await handler.handle(command)
        assert len(result) == 1
        assert result[0].expedient_id == "uuid-high"

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_raises_download_error_on_api_failure(self):
        """handle() must raise DownloadError when the API raises an exception."""
        handler, api, _ = self._make_handler()
        api.fetch_page.side_effect = Exception("Connection timeout")
        command = DownloadTendersCommand(filter_config=_make_filter_config())
        with pytest.raises(DownloadError):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_download_error_contains_original_message(self):
        """DownloadError message must include the original exception info."""
        handler, api, _ = self._make_handler()
        api.fetch_page.side_effect = Exception("Connection timeout")
        command = DownloadTendersCommand(filter_config=_make_filter_config())
        with pytest.raises(DownloadError, match="Connection timeout"):
            await handler.handle(command)

    # ------------------------------------------------------------------
    # Fetch detail for null pressupost (6.2)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_fetches_detail_when_pressupost_is_null(self):
        """When pressupostLicitacio is null, handle() must call api.fetch_detail()."""
        item = _make_api_tender("uuid-null", pressupost=None)
        item["pressupostLicitacio"] = None
        handler, api, _ = self._make_handler(api_return=[item])
        api.fetch_detail = AsyncMock(return_value={"pressupostLicitacio": 450_000.0})

        command = DownloadTendersCommand(filter_config=_make_filter_config())
        await handler.handle(command)

        api.fetch_detail.assert_called_once_with("uuid-null", 42)

    @pytest.mark.asyncio
    async def test_uses_pressupost_from_detail_when_listing_is_null(self):
        """When listing has null pressupost, the Tender must use the detail value."""
        item = _make_api_tender("uuid-null", pressupost=None)
        item["pressupostLicitacio"] = None
        handler, api, _ = self._make_handler(api_return=[item])
        api.fetch_detail = AsyncMock(return_value={"pressupostLicitacio": 450_000.0})

        command = DownloadTendersCommand(filter_config=_make_filter_config())
        result = await handler.handle(command)

        assert len(result) == 1
        assert result[0].pressupost == 450_000.0

    @pytest.mark.asyncio
    async def test_does_not_fetch_detail_when_pressupost_present(self):
        """When pressupostLicitacio has a value, fetch_detail must NOT be called."""
        handler, api, _ = self._make_handler(
            api_return=[_make_api_tender("uuid-ok", pressupost=300_000.0)]
        )
        api.fetch_detail = AsyncMock()

        command = DownloadTendersCommand(filter_config=_make_filter_config())
        await handler.handle(command)

        api.fetch_detail.assert_not_called()

    @pytest.mark.asyncio
    async def test_uses_zero_if_detail_also_has_null_pressupost(self):
        """If both listing and detail have null pressupost, use 0.0 as fallback."""
        item = _make_api_tender("uuid-null")
        item["pressupostLicitacio"] = None
        handler, api, _ = self._make_handler(api_return=[item])
        api.fetch_detail = AsyncMock(return_value={"pressupostLicitacio": None})

        command = DownloadTendersCommand(filter_config=_make_filter_config())
        result = await handler.handle(command)

        assert result[0].pressupost == 0.0
