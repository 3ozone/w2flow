"""Unit tests for the Score value object."""
import pytest

from app.domain.value_objects.score import Score
from app.domain.value_objects.traffic_light import TrafficLight


class TestScore:
    """Tests for the Score value object."""

    def _make_score(self, total: int = 40) -> Score:
        """Helper to build a minimal valid Score."""
        return Score(
            expedient_id="uuid-123",
            total=total,
            detall={
                "pressupost": 20,
                "sector_positiu": 15,
                "sector_negatiu": 0,
                "procediment_obert": 10,
                "subcontractació": 5,
            },
            paraules_clau_trobades=["obres", "infraestructura"],
            penalitzacions=[],
            recomanacio="⚠️ A VALORAR",
        )

    # ------------------------------------------------------------------
    # assign_traffic_light()
    # ------------------------------------------------------------------

    def test_assign_traffic_light_returns_green_at_50(self):
        """assign_traffic_light() must return GREEN when total == 50."""
        score = self._make_score(total=50)
        assert score.assign_traffic_light() == TrafficLight.GREEN

    def test_assign_traffic_light_returns_green_above_50(self):
        """assign_traffic_light() must return GREEN when total > 50."""
        score = self._make_score(total=70)
        assert score.assign_traffic_light() == TrafficLight.GREEN

    def test_assign_traffic_light_returns_yellow_at_25(self):
        """assign_traffic_light() must return YELLOW when total == 25."""
        score = self._make_score(total=25)
        assert score.assign_traffic_light() == TrafficLight.YELLOW

    def test_assign_traffic_light_returns_yellow_below_50(self):
        """assign_traffic_light() must return YELLOW when 25 <= total < 50."""
        score = self._make_score(total=49)
        assert score.assign_traffic_light() == TrafficLight.YELLOW

    def test_assign_traffic_light_returns_red_below_25(self):
        """assign_traffic_light() must return RED when total < 25."""
        score = self._make_score(total=24)
        assert score.assign_traffic_light() == TrafficLight.RED

    def test_assign_traffic_light_returns_red_at_zero(self):
        """assign_traffic_light() must return RED when total == 0."""
        score = self._make_score(total=0)
        assert score.assign_traffic_light() == TrafficLight.RED

    # ------------------------------------------------------------------
    # is_viable()
    # ------------------------------------------------------------------

    def test_is_viable_returns_true_when_total_at_25(self):
        """is_viable() must return True when total == 25 (YELLOW threshold)."""
        score = self._make_score(total=25)
        assert score.is_viable() is True

    def test_is_viable_returns_true_when_total_above_25(self):
        """is_viable() must return True when total > 25."""
        score = self._make_score(total=60)
        assert score.is_viable() is True

    def test_is_viable_returns_false_when_total_below_25(self):
        """is_viable() must return False when total < 25 (RED)."""
        score = self._make_score(total=24)
        assert score.is_viable() is False

    def test_is_viable_returns_false_at_zero(self):
        """is_viable() must return False when total == 0."""
        score = self._make_score(total=0)
        assert score.is_viable() is False

    # ------------------------------------------------------------------
    # to_report()
    # ------------------------------------------------------------------

    def test_to_report_contains_expedient_id(self):
        """to_report() must include 'expedient_id'."""
        score = self._make_score()
        assert "expedient_id" in score.to_report()

    def test_to_report_contains_total(self):
        """to_report() must include 'total'."""
        score = self._make_score(total=40)
        assert score.to_report()["total"] == 40

    def test_to_report_contains_traffic_light(self):
        """to_report() must include 'traffic_light' as a string value."""
        score = self._make_score(total=50)
        report = score.to_report()
        assert "traffic_light" in report
        assert report["traffic_light"] == TrafficLight.GREEN.value

    def test_to_report_contains_recomanacio(self):
        """to_report() must include 'recomanacio'."""
        score = self._make_score()
        assert "recomanacio" in score.to_report()

    def test_to_report_contains_detall(self):
        """to_report() must include 'detall' with the score breakdown."""
        score = self._make_score()
        assert "detall" in score.to_report()

    # ------------------------------------------------------------------
    # Immutability (frozen dataclass)
    # ------------------------------------------------------------------

    def test_score_is_immutable(self):
        """Score must be immutable (frozen dataclass)."""
        score = self._make_score()
        with pytest.raises((AttributeError, TypeError)):
            score.total = 99  # type: ignore[misc]

    def test_two_scores_with_same_values_are_equal(self):
        """Two Score instances with identical values must be equal."""
        a = self._make_score(total=40)
        b = self._make_score(total=40)
        assert a == b

    def test_two_scores_with_different_totals_are_not_equal(self):
        """Two Score instances with different totals must not be equal."""
        a = self._make_score(total=40)
        b = self._make_score(total=60)
        assert a != b
