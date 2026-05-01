"""Unit tests for the ComparativeReport entity."""
from datetime import date

from app.domain.entities.comparative_report import ComparativeReport
from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.value_objects.filter_config import FilterConfig
from app.domain.value_objects.score import Score


class TestComparativeReport:
    """Tests for the ComparativeReport entity."""

    def _make_tender(self, expedient_id: str, pressupost: float = 100_000.0) -> Tender:
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

    def _make_score(self, expedient_id: str, total: int) -> Score:
        return Score(
            expedient_id=expedient_id,
            total=total,
            detall={},
            paraules_clau_trobades=(),
            penalitzacions=(),
            recomanacio="Viable" if total >= 25 else "No viable",
        )

    def _make_scored_tender(self, expedient_id: str, total: int) -> ScoredTender:
        return ScoredTender(
            tender=self._make_tender(expedient_id),
            score=self._make_score(expedient_id, total),
            requirements=None,
        )

    def _make_filter_config(self) -> FilterConfig:
        return FilterConfig(
            tipus_expedient=1,
            fase_vigent=0,
            sector_keywords=("construcció", "obra"),
        )

    def _make_report(self, scored_tenders: list[ScoredTender] | None = None) -> ComparativeReport:
        if scored_tenders is None:
            scored_tenders = [
                self._make_scored_tender("uuid-go-1", total=60),
                self._make_scored_tender("uuid-go-2", total=30),
                self._make_scored_tender("uuid-no-go", total=10),
            ]
        return ComparativeReport(
            scored_tenders=scored_tenders,
            filter_config=self._make_filter_config(),
        )

    # ------------------------------------------------------------------
    # get_viable_tenders()
    # ------------------------------------------------------------------

    def test_get_viable_tenders_returns_only_go_tenders(self):
        """get_viable_tenders() must return only tenders where is_go() is True."""
        report = self._make_report()
        viable = report.get_viable_tenders()
        assert len(viable) == 2

    def test_get_viable_tenders_excludes_non_viable(self):
        """get_viable_tenders() must exclude tenders where is_go() is False."""
        report = self._make_report()
        viable = report.get_viable_tenders()
        assert all(st.is_go() for st in viable)

    def test_get_viable_tenders_returns_empty_when_all_non_viable(self):
        """get_viable_tenders() must return empty list when no tender is viable."""
        report = self._make_report([
            self._make_scored_tender("uuid-a", total=5),
            self._make_scored_tender("uuid-b", total=10),
        ])
        assert report.get_viable_tenders() == []

    def test_get_viable_tenders_returns_all_when_all_viable(self):
        """get_viable_tenders() must return all tenders when all are viable."""
        report = self._make_report([
            self._make_scored_tender("uuid-a", total=50),
            self._make_scored_tender("uuid-b", total=60),
        ])
        assert len(report.get_viable_tenders()) == 2

    # ------------------------------------------------------------------
    # generate_json()
    # ------------------------------------------------------------------

    def test_generate_json_contains_total_count(self):
        """generate_json() must include 'total_count'."""
        report = self._make_report()
        data = report.generate_json()
        assert "total_count" in data
        assert data["total_count"] == 3

    def test_generate_json_contains_viable_count(self):
        """generate_json() must include 'viable_count'."""
        report = self._make_report()
        data = report.generate_json()
        assert "viable_count" in data
        assert data["viable_count"] == 2

    def test_generate_json_contains_tenders_list(self):
        """generate_json() must include a 'tenders' list."""
        report = self._make_report()
        data = report.generate_json()
        assert "tenders" in data
        assert isinstance(data["tenders"], list)
        assert len(data["tenders"]) == 3

    def test_generate_json_tenders_contain_summary_fields(self):
        """Each tender in generate_json()['tenders'] must have summary fields."""
        report = self._make_report()
        for tender_data in report.generate_json()["tenders"]:
            assert "expedient_id" in tender_data
            assert "total_score" in tender_data
            assert "is_go" in tender_data

    def test_generate_json_contains_filter_config(self):
        """generate_json() must include 'filter_config'."""
        report = self._make_report()
        assert "filter_config" in report.generate_json()
