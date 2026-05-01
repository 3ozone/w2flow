"""Tests for FilterTendersCommandHandler."""

from datetime import date

from app.application.use_cases.commands.filter_tenders_command import (
    FilterTendersCommand,
    FilterTendersCommandHandler,
)
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


def _make_tender(expedient_id: str = "uuid-1", pressupost: float = 100_000.0) -> Tender:
    return Tender(
        expedient_id=expedient_id,
        publicacio_id=1,
        titol=f"Licitació {expedient_id}",
        organ="Ajuntament de Barcelona",
        pressupost=pressupost,
        codi_expedient=f"EXP-{expedient_id}",
        fase="0",
        data_publicacio=date.today(),
    )


class TestFilterTendersCommandHandler:
    """Tests for FilterTendersCommandHandler."""

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_returns_all_when_no_min_pressupost(self):
        """handle() must return all tenders when min_pressupost is 0."""
        tenders = [_make_tender("uuid-1", 10_000.0),
                   _make_tender("uuid-2", 500_000.0)]
        command = FilterTendersCommand(
            tenders=tenders,
            filter_config=_make_filter_config(min_pressupost=0.0),
        )
        result = FilterTendersCommandHandler().handle(command)
        assert len(result) == 2

    def test_filters_below_min_pressupost(self):
        """handle() must exclude tenders with pressupost below min_pressupost."""
        tenders = [
            _make_tender("uuid-high", pressupost=200_000.0),
            _make_tender("uuid-low", pressupost=5_000.0),
        ]
        command = FilterTendersCommand(
            tenders=tenders,
            filter_config=_make_filter_config(min_pressupost=50_000.0),
        )
        result = FilterTendersCommandHandler().handle(command)
        assert len(result) == 1
        assert result[0].expedient_id == "uuid-high"

    def test_returns_empty_when_all_below_threshold(self):
        """handle() must return empty list when all tenders are below threshold."""
        tenders = [_make_tender("uuid-a", 100.0),
                   _make_tender("uuid-b", 200.0)]
        command = FilterTendersCommand(
            tenders=tenders,
            filter_config=_make_filter_config(min_pressupost=10_000.0),
        )
        result = FilterTendersCommandHandler().handle(command)
        assert result == []

    def test_returns_empty_when_input_is_empty(self):
        """handle() must return empty list when given no tenders."""
        command = FilterTendersCommand(
            tenders=[],
            filter_config=_make_filter_config(),
        )
        result = FilterTendersCommandHandler().handle(command)
        assert result == []

    def test_includes_tender_at_exact_threshold(self):
        """handle() must include tenders with pressupost == min_pressupost."""
        tenders = [_make_tender("uuid-exact", pressupost=50_000.0)]
        command = FilterTendersCommand(
            tenders=tenders,
            filter_config=_make_filter_config(min_pressupost=50_000.0),
        )
        result = FilterTendersCommandHandler().handle(command)
        assert len(result) == 1

    def test_returns_list_of_tender_instances(self):
        """handle() must return a list of Tender instances."""
        command = FilterTendersCommand(
            tenders=[_make_tender()],
            filter_config=_make_filter_config(),
        )
        result = FilterTendersCommandHandler().handle(command)
        assert all(isinstance(t, Tender) for t in result)
