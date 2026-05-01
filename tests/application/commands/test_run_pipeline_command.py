"""Tests for RunPipelineCommandHandler."""

from datetime import date
from unittest.mock import AsyncMock
import pytest

from app.domain.entities.comparative_report import ComparativeReport
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
        "titol": f"Obres de construcció {expedient_id}",
        "organ": "Ajuntament de Barcelona",
        "pressupostLicitacio": pressupost,
        "codiExpedient": f"EXP-{expedient_id}",
        "fasesVigents": {"0": {"dataPublicacio": date.today().isoformat()}},
    }


class TestRunPipelineCommandHandler:
    """Tests for RunPipelineCommandHandler.

    Validates that the handler orchestrates download→filter→score→report
    and returns a ComparativeReport without any presentation-layer coupling.
    """

    def _make_handler(self, api_items: list[dict] | None = None):
        from app.application.use_cases.commands.run_pipeline_command import (
            RunPipelineCommand,
            RunPipelineCommandHandler,
        )

        api = AsyncMock()
        api.fetch_page.return_value = api_items if api_items is not None else []
        api.fetch_detail.return_value = {}
        api.fetch_documents.return_value = []
        api.download_document.return_value = b""

        repository = AsyncMock()
        repository.save.return_value = None
        repository.save_scored.return_value = None

        storage = AsyncMock()
        storage.exists.return_value = False
        storage.save.return_value = "downloads/uuid-1/doc.pdf"

        filter_config = _make_filter_config()
        handler = RunPipelineCommandHandler(
            api=api, repository=repository, storage=storage)
        command = RunPipelineCommand(filter_config=filter_config)
        return handler, command, api, repository, storage

    # ------------------------------------------------------------------
    # Return type
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_returns_comparative_report(self):
        """handle() must return a ComparativeReport instance."""
        handler, command, _, _, _ = self._make_handler(
            api_items=[_make_api_tender()]
        )
        result = await handler.handle(command)
        assert isinstance(result, ComparativeReport)

    # ------------------------------------------------------------------
    # Empty pipeline
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_empty_api_returns_report_with_no_scored_tenders(self):
        """When the API returns no tenders the report has an empty scored_tenders list."""
        handler, command, _, _, _ = self._make_handler(api_items=[])
        result = await handler.handle(command)
        assert isinstance(result, ComparativeReport)
        assert result.scored_tenders == []

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_calls_api_fetch_page(self):
        """handle() must call api.fetch_page at least once."""
        handler, command, api, _, _ = self._make_handler(
            api_items=[_make_api_tender()]
        )
        await handler.handle(command)
        api.fetch_page.assert_called()

    @pytest.mark.asyncio
    async def test_saves_each_tender_to_repository(self):
        """handle() must persist each downloaded tender via repository.save()."""
        handler, command, _, repository, _ = self._make_handler(
            api_items=[_make_api_tender("uuid-1"), _make_api_tender("uuid-2")]
        )
        await handler.handle(command)
        assert repository.save.call_count == 2

    @pytest.mark.asyncio
    async def test_report_contains_scored_tender_for_each_downloaded_tender(self):
        """The returned ComparativeReport must contain one ScoredTender per downloaded tender."""
        handler, command, _, _, _ = self._make_handler(
            api_items=[_make_api_tender("uuid-1"), _make_api_tender("uuid-2")]
        )
        result = await handler.handle(command)
        assert len(result.scored_tenders) == 2

    # ------------------------------------------------------------------
    # No presentation coupling
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_handler_does_not_import_presentation_layer(self):
        """RunPipelineCommandHandler must not depend on any infrastructure.api module."""
        import sys

        # Remove cached module to force a clean import
        for key in list(sys.modules.keys()):
            if "run_pipeline_command" in key:
                del sys.modules[key]

        import app.application.use_cases.commands.run_pipeline_command as mod
        source_file = mod.__file__ or ""
        with open(source_file) as f:
            source = f.read()

        assert "infrastructure.api" not in source, (
            "RunPipelineCommandHandler must not import from infrastructure.api"
        )
        assert "reports_router" not in source, (
            "RunPipelineCommandHandler must not reference reports_router"
        )

    # ------------------------------------------------------------------
    # Document download stage
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_calls_fetch_documents_for_each_tender(self):
        """handle() must call api.fetch_documents() once per filtered tender."""
        handler, command, api, _, _ = self._make_handler(
            api_items=[_make_api_tender("uuid-1"), _make_api_tender("uuid-2")]
        )
        await handler.handle(command)
        assert api.fetch_documents.call_count == 2

    @pytest.mark.asyncio
    async def test_downloads_valid_documents_for_each_tender(self):
        """handle() must download non-UNKNOWN documents via api.download_document()."""
        from app.application.use_cases.commands.run_pipeline_command import (
            RunPipelineCommand,
            RunPipelineCommandHandler,
        )

        api = AsyncMock()
        api.fetch_page.return_value = [_make_api_tender("uuid-1")]
        api.fetch_detail.return_value = {}
        api.fetch_documents.return_value = [
            {"id": 1, "titol": "PCAP_exp.pdf", "hash": "abc", "midaKb": 100.0}
        ]
        api.download_document.return_value = b"%PDF"

        repository = AsyncMock()
        repository.save.return_value = None
        repository.save_scored.return_value = None

        storage = AsyncMock()
        storage.exists.return_value = False
        storage.save.return_value = "downloads/uuid-1/PCAP_exp.pdf"

        handler = RunPipelineCommandHandler(
            api=api, repository=repository, storage=storage)
        command = RunPipelineCommand(filter_config=_make_filter_config())
        await handler.handle(command)

        api.download_document.assert_called_once()
        storage.save.assert_called_once()
