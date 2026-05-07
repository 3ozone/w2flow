"""Unit tests for the ScoredTender entity."""
from datetime import date

from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.value_objects.score import Score


class TestScoredTender:
    """Tests for the ScoredTender entity."""

    def _make_tender(self, expedient_id: str = "uuid-abc-123") -> Tender:
        return Tender(
            expedient_id=expedient_id,
            publicacio_id=42,
            titol="Obres de construcció de la nova biblioteca",
            organ="Ajuntament de Barcelona",
            pressupost=250_000.0,
            codi_expedient="EXP-2026-001",
            fase="0",
            data_publicacio=date.today(),
        )

    def _make_score(self, total: int = 55) -> Score:
        return Score(
            expedient_id="uuid-abc-123",
            total=total,
            detall={"sector_positiu": 30, "pressupost": 25},
            paraules_clau_trobades=("construcció", "obra"),
            penalitzacions=(),
            recomanacio="Viable",
        )

    def _make_scored_tender(self, total: int = 55, **kwargs) -> ScoredTender:
        return ScoredTender(
            tender=self._make_tender(),
            score=self._make_score(total=total),
            requirements=None,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # is_go()
    # ------------------------------------------------------------------

    def test_is_go_returns_true_when_score_is_viable(self):
        """is_go() must return True when score.total >= 25."""
        st = self._make_scored_tender(total=55)
        assert st.is_go() is True

    def test_is_go_returns_true_at_boundary_40(self):
        """is_go() must return True when score.total == 40 (YELLOW threshold, RN-03)."""
        st = self._make_scored_tender(total=40)
        assert st.is_go() is True

    def test_is_go_returns_false_when_score_is_not_viable(self):
        """is_go() must return False when score.total < 40."""
        st = self._make_scored_tender(total=39)
        assert st.is_go() is False

    def test_is_go_delegates_to_score_is_viable(self):
        """is_go() result must match score.is_viable()."""
        for total in [0, 24, 25, 49, 50, 70]:
            st = self._make_scored_tender(total=total)
            assert st.is_go() == st.score.is_viable()

    # ------------------------------------------------------------------
    # get_summary()
    # ------------------------------------------------------------------

    def test_get_summary_contains_expedient_id(self):
        """get_summary() must include 'expedient_id'."""
        st = self._make_scored_tender()
        assert "expedient_id" in st.get_summary()

    def test_get_summary_contains_titol(self):
        """get_summary() must include 'titol'."""
        st = self._make_scored_tender()
        assert "titol" in st.get_summary()

    def test_get_summary_contains_organ(self):
        """get_summary() must include 'organ'."""
        st = self._make_scored_tender()
        assert "organ" in st.get_summary()

    def test_get_summary_contains_pressupost(self):
        """get_summary() must include 'pressupost'."""
        st = self._make_scored_tender()
        assert "pressupost" in st.get_summary()

    def test_get_summary_contains_total_score(self):
        """get_summary() must include 'total_score'."""
        st = self._make_scored_tender(total=55)
        summary = st.get_summary()
        assert "total_score" in summary
        assert summary["total_score"] == 55

    def test_get_summary_contains_traffic_light(self):
        """get_summary() must include 'traffic_light'."""
        st = self._make_scored_tender()
        assert "traffic_light" in st.get_summary()

    def test_get_summary_contains_is_go(self):
        """get_summary() must include 'is_go'."""
        st = self._make_scored_tender(total=55)
        summary = st.get_summary()
        assert "is_go" in summary
        assert summary["is_go"] is True
