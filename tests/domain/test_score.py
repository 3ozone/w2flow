"""Tests for Score value object (RN-03)."""
from app.domain.value_objects.score import Score
from app.domain.value_objects.traffic_light import TrafficLight


def _make_score(total: int) -> Score:
    """Helper to build a minimal Score."""
    return Score(expedient_id="exp-1", total=total, detall={})


def test_is_viable():
    """Score >= 40 is viable (GO)."""
    assert _make_score(40).is_viable() is True


def test_is_not_viable():
    """Score < 40 is not viable (NO GO)."""
    assert _make_score(39).is_viable() is False


def test_assign_traffic_light():
    """Traffic light delegates to TrafficLight.from_score()."""
    assert _make_score(70).assign_traffic_light() == TrafficLight.GREEN
