"""Tests for GetComparativeReportQueryHandler."""

from datetime import date
from unittest.mock import AsyncMock
import pytest

from app.application.use_cases.queries.get_comparative_report_query import (
    GetComparativeReportQuery,
    GetComparativeReportQueryHandler,
)
from app.domain.entities.comparative_report import ComparativeReport
from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.value_objects.filter_config import FilterConfig
from app.domain.value_objects.score import Score


def _make_filter_config() -> FilterConfig:
    return FilterConfig(
        tipus_expedient=1,
        fase_vigent=0,
        sector_keywords=("construcció",),
    )


def _make_scored_tender(expedient_id: str = "uuid-1", total: int = 60) -> ScoredTender:
    tender = Tender(
        expedient_id=expedient_id,
        publicacio_id=1,
        titol="Obres de construcció",
        organ="Ajuntament de Barcelona",
        pressupost=500_000.0,
        codi_expedient=f"EXP-{expedient_id}",
        fase="0",
        data_publicacio=date.today(),
    )
    score = Score(
        expedient_id=expedient_id,
        total=total,
        detall={"pressupost": 20, "sector_positiu": 10, "sector_negatiu": 0},
        paraules_clau_trobades=("construcció",),
        penalitzacions=(),
        recomanacio="RECOMANADA",
    )
    return ScoredTender(tender=tender, score=score, requirements=None)


class TestGetComparativeReportQueryHandler:
    """Tests for GetComparativeReportQueryHandler."""

    def _make_handler(self, scored_tenders: list[ScoredTender] | None = None):
        repository = AsyncMock()
        repository.list_scored.return_value = scored_tenders or []
        return GetComparativeReportQueryHandler(repository=repository), repository

    # ------------------------------------------------------------------
    # Return type
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_returns_comparative_report_instance(self):
        """handle() must return a ComparativeReport instance."""
        handler, _ = self._make_handler()
        query = GetComparativeReportQuery(filter_config=_make_filter_config())
        result = await handler.handle(query)
        assert isinstance(result, ComparativeReport)

    @pytest.mark.asyncio
    async def test_report_has_correct_filter_config(self):
        """The returned report must carry the filter_config from the query."""
        handler, _ = self._make_handler()
        fc = _make_filter_config()
        query = GetComparativeReportQuery(filter_config=fc)
        result = await handler.handle(query)
        assert result.filter_config == fc

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_report_scored_tenders_match_repository(self):
        """The report must contain exactly the tenders returned by the repository."""
        scored = [_make_scored_tender("uuid-1"), _make_scored_tender("uuid-2")]
        handler, _ = self._make_handler(scored)
        query = GetComparativeReportQuery(filter_config=_make_filter_config())
        result = await handler.handle(query)
        assert result.scored_tenders == scored

    @pytest.mark.asyncio
    async def test_report_is_empty_when_repository_empty(self):
        """The report must have zero tenders when repository returns none."""
        handler, _ = self._make_handler([])
        query = GetComparativeReportQuery(filter_config=_make_filter_config())
        result = await handler.handle(query)
        assert result.scored_tenders == []

    # ------------------------------------------------------------------
    # Delegation to repository
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_delegates_to_repository(self):
        """handle() must call repository.list_scored()."""
        handler, repository = self._make_handler()
        query = GetComparativeReportQuery(filter_config=_make_filter_config())
        await handler.handle(query)
        repository.list_scored.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_default_pagination(self):
        """Default query uses page=0, size=20."""
        handler, repository = self._make_handler()
        query = GetComparativeReportQuery(filter_config=_make_filter_config())
        await handler.handle(query)
        repository.list_scored.assert_called_once_with(page=0, size=20)

    @pytest.mark.asyncio
    async def test_passes_custom_pagination(self):
        """Custom page/size are forwarded to the repository."""
        handler, repository = self._make_handler()
        query = GetComparativeReportQuery(
            filter_config=_make_filter_config(), page=3, size=10
        )
        await handler.handle(query)
        repository.list_scored.assert_called_once_with(page=3, size=10)

    # ------------------------------------------------------------------
    # generate_json integration
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_generate_json_returns_expected_structure(self):
        """generate_json() on the result must include total_count and viable_count."""
        scored = [_make_scored_tender("uuid-1", total=60)]
        handler, _ = self._make_handler(scored)
        query = GetComparativeReportQuery(filter_config=_make_filter_config())
        result = await handler.handle(query)
        report_json = result.generate_json()
        assert "total_count" in report_json
        assert "viable_count" in report_json
        assert report_json["total_count"] == 1
