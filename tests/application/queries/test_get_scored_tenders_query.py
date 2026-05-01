"""Tests for GetScoredTendersQueryHandler."""

from datetime import date
from unittest.mock import AsyncMock
import pytest

from app.application.use_cases.queries.get_scored_tenders_query import (
    GetScoredTendersQuery,
    GetScoredTendersQueryHandler,
)
from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.value_objects.score import Score


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
        paraules_clau_trobades=("obres",),
        penalitzacions=(),
        recomanacio="RECOMANADA",
    )
    return ScoredTender(tender=tender, score=score, requirements=None)


class TestGetScoredTendersQueryHandler:
    """Tests for GetScoredTendersQueryHandler."""

    def _make_handler(self, scored_tenders: list[ScoredTender] | None = None):
        repository = AsyncMock()
        repository.list_scored.return_value = scored_tenders or []
        return GetScoredTendersQueryHandler(repository=repository), repository

    # ------------------------------------------------------------------
    # Return type
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_returns_list(self):
        """handle() must return a list."""
        handler, _ = self._make_handler()
        result = await handler.handle(GetScoredTendersQuery())
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_returns_scored_tender_instances(self):
        """Items in the list must be ScoredTender instances."""
        scored = _make_scored_tender()
        handler, _ = self._make_handler([scored])
        result = await handler.handle(GetScoredTendersQuery())
        assert all(isinstance(item, ScoredTender) for item in result)

    # ------------------------------------------------------------------
    # Delegation to repository
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_delegates_to_repository(self):
        """handle() must call repository.list_scored()."""
        handler, repository = self._make_handler()
        await handler.handle(GetScoredTendersQuery())
        repository.list_scored.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_default_pagination(self):
        """Default query uses page=0, size=20."""
        handler, repository = self._make_handler()
        await handler.handle(GetScoredTendersQuery())
        repository.list_scored.assert_called_once_with(page=0, size=20)

    @pytest.mark.asyncio
    async def test_passes_custom_pagination(self):
        """Custom page/size are forwarded to the repository."""
        handler, repository = self._make_handler()
        await handler.handle(GetScoredTendersQuery(page=2, size=5))
        repository.list_scored.assert_called_once_with(page=2, size=5)

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_returns_all_items_from_repository(self):
        """handle() must return exactly the items the repository returns."""
        scored = [_make_scored_tender("uuid-1"), _make_scored_tender("uuid-2")]
        handler, _ = self._make_handler(scored)
        result = await handler.handle(GetScoredTendersQuery())
        assert result == scored

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_repository_empty(self):
        """handle() must return an empty list when repository has no data."""
        handler, _ = self._make_handler([])
        result = await handler.handle(GetScoredTendersQuery())
        assert result == []
