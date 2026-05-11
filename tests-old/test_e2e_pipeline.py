"""End-to-end tests for the full pipeline: download → filter → score → report.

These tests use:
- Real domain logic (FilterConfig, Score, Tender, ScoredTender, ComparativeReport)
- Real command and query handlers
- An in-memory TenderRepositoryPort implementation (no DB, no external APIs)
- A mocked LicitationApiPort (no HTTP calls)

Validates: RN-05 (expired discarded), RN-06 (deduplication), R-03 (< 60s).
"""

from __future__ import annotations

import asyncio
import time
from datetime import date

import pytest

from app.application.ports.licitacion_api_port import LicitationApiPort
from app.application.ports.tender_repository_port import TenderRepositoryPort
from app.application.use_cases.commands.download_tenders_command import (
    DownloadTendersCommand,
    DownloadTendersCommandHandler,
)
from app.application.use_cases.commands.filter_tenders_command import (
    FilterTendersCommand,
    FilterTendersCommandHandler,
)
from app.application.use_cases.commands.score_tender_command import (
    ScoreTenderCommand,
    ScoreTenderCommandHandler,
)
from app.application.use_cases.queries.get_comparative_report_query import (
    GetComparativeReportQuery,
    GetComparativeReportQueryHandler,
)
from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.exceptions.duplicate_tender_error import DuplicateTenderError
from app.domain.value_objects.filter_config import FilterConfig


# ---------------------------------------------------------------------------
# In-memory repository (no DB required for e2e tests)
# ---------------------------------------------------------------------------


class InMemoryTenderRepository(TenderRepositoryPort):
    """Fully in-memory implementation of TenderRepositoryPort for testing."""

    def __init__(self) -> None:
        self._tenders: dict[str, Tender] = {}
        self._scored: dict[str, ScoredTender] = {}

    async def save(self, tender: Tender) -> None:
        if tender.expedient_id in self._tenders:
            raise DuplicateTenderError(tender.expedient_id)
        self._tenders[tender.expedient_id] = tender

    async def get_by_id(self, expedient_id: str) -> Tender | None:
        return self._tenders.get(expedient_id)

    async def save_scored(self, scored_tender: ScoredTender) -> None:
        self._scored[scored_tender.tender.expedient_id] = scored_tender

    async def list_scored(self, page: int = 0, size: int = 20) -> list[ScoredTender]:
        items = list(self._scored.values())
        start = page * size
        return items[start: start + size]


# ---------------------------------------------------------------------------
# API stub helpers
# ---------------------------------------------------------------------------

def _api_item(
    expedient_id: str,
    pressupost: float = 500_000.0,
    titol: str = "Obres de pavimentació",
    data_publicacio: str = "2026-05-01",
) -> dict:
    """Build a minimal raw API response item."""
    return {
        "expedientId": expedient_id,
        "id": 42,
        "titol": titol,
        "organ": "Ajuntament de Girona",
        "pressupostLicitacio": pressupost,
        "codiExpedient": "EXP-001",
        "fase": "0",
        "dataPublicacio": data_publicacio,
    }


class StubLicitationApi(LicitationApiPort):
    """Returns a fixed list of raw tender items."""

    def __init__(self, items: list[dict]) -> None:
        self._items = items

    async def fetch_page(self, filter_config: FilterConfig, page: int) -> list[dict]:
        return self._items

    async def fetch_detail(self, expedient_id: str, publicacio_id: int) -> dict:
        return {}

    async def download_document(self, doc_id: int, doc_hash: str) -> bytes:
        return b""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def repository() -> InMemoryTenderRepository:
    return InMemoryTenderRepository()


@pytest.fixture
def filter_config() -> FilterConfig:
    return FilterConfig(
        tipus_expedient=1,
        fase_vigent=0,
        sector_keywords=("obres", "construcció"),
        min_pressupost=100_000.0,
    )


# ---------------------------------------------------------------------------
# Helper: run full pipeline (download → filter → score → report)
# ---------------------------------------------------------------------------


async def _run_pipeline(
    api_items: list[dict],
    repository: InMemoryTenderRepository,
    filter_config: FilterConfig,
) -> list[ScoredTender]:
    """Execute the three-stage pipeline and return scored tenders."""
    # Stage 1: download & save
    download_handler = DownloadTendersCommandHandler(
        api=StubLicitationApi(api_items),
        repository=repository,
    )
    tenders = await download_handler.handle(DownloadTendersCommand(filter_config))

    # Stage 2: filter (in-memory fine-grained)
    filter_handler = FilterTendersCommandHandler()
    filtered = filter_handler.handle(
        FilterTendersCommand(tenders, filter_config))

    # Stage 3: score & persist
    score_handler = ScoreTenderCommandHandler(repository=repository)
    for tender in filtered:
        await score_handler.handle(
            ScoreTenderCommand(
                tender=tender, filter_config=filter_config, pdf_texts=[])
        )

    return await repository.list_scored()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEndToEndPipeline:
    """Full pipeline integration tests with in-memory dependencies."""

    @pytest.mark.asyncio
    async def test_pipeline_produces_scored_tenders(self, repository, filter_config):
        """A valid tender passes all stages and appears in list_scored."""
        items = [_api_item("uuid-1", pressupost=500_000.0)]
        scored = await _run_pipeline(items, repository, filter_config)
        assert len(scored) == 1
        assert scored[0].tender.expedient_id == "uuid-1"

    @pytest.mark.asyncio
    async def test_score_is_calculated(self, repository, filter_config):
        """The scored tender has a non-negative total score."""
        items = [_api_item("uuid-2", pressupost=500_000.0)]
        scored = await _run_pipeline(items, repository, filter_config)
        assert scored[0].score.total >= 0

    @pytest.mark.asyncio
    async def test_pipeline_builds_comparative_report(self, repository, filter_config):
        """GetComparativeReportQueryHandler wraps scored tenders in a report."""
        items = [
            _api_item("uuid-3", pressupost=500_000.0),
            _api_item("uuid-4", pressupost=600_000.0),
        ]
        await _run_pipeline(items, repository, filter_config)

        query_handler = GetComparativeReportQueryHandler(repository=repository)
        report = await query_handler.handle(
            GetComparativeReportQuery(filter_config=filter_config)
        )
        assert len(report.scored_tenders) == 2
        assert report.generate_json()["total_count"] == 2

    @pytest.mark.asyncio
    async def test_rn05_low_budget_tender_is_discarded(self, repository, filter_config):
        """RN-05: tenders below min_pressupost are discarded by FilterConfig.matches()."""
        items = [
            _api_item("uuid-ok", pressupost=500_000.0),
            # below 100_000 threshold
            _api_item("uuid-low", pressupost=50_000.0),
        ]
        scored = await _run_pipeline(items, repository, filter_config)
        ids = [st.tender.expedient_id for st in scored]
        assert "uuid-ok" in ids
        assert "uuid-low" not in ids

    @pytest.mark.asyncio
    async def test_rn06_duplicate_tender_is_not_saved_twice(self, repository, filter_config):
        """RN-06: attempting to download the same tender twice raises DuplicateTenderError."""
        api = StubLicitationApi([_api_item("uuid-dup")])
        handler = DownloadTendersCommandHandler(api=api, repository=repository)
        cmd = DownloadTendersCommand(filter_config)

        await handler.handle(cmd)  # first run — OK

        with pytest.raises(DuplicateTenderError):
            await handler.handle(cmd)  # second run — duplicate

    @pytest.mark.asyncio
    async def test_r03_pipeline_completes_in_under_60_seconds(
        self, repository, filter_config
    ):
        """R-03: the in-process pipeline must complete in under 60 seconds."""
        items = [_api_item(f"uuid-{i}", pressupost=200_000.0)
                 for i in range(20)]
        start = time.monotonic()
        await _run_pipeline(items, repository, filter_config)
        elapsed = time.monotonic() - start
        assert elapsed < 60, f"Pipeline took {elapsed:.2f}s — exceeds 60s limit"
