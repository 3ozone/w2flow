"""Unit tests for the TrafficLight enum and its from_score method."""
import pytest

from app.domain.value_objects.traffic_light import TrafficLight


class TestTrafficLight:
    """Tests for the TrafficLight enum and its threshold logic."""

    def test_green_value_exists(self):
        """GREEN member must exist."""
        assert TrafficLight.GREEN is not None

    def test_yellow_value_exists(self):
        """YELLOW member must exist."""
        assert TrafficLight.YELLOW is not None

    def test_red_value_exists(self):
        """RED member must exist."""
        assert TrafficLight.RED is not None

    def test_has_exactly_three_members(self):
        """Enum must contain exactly three members: GREEN, YELLOW, RED."""
        assert len(TrafficLight) == 3

    def test_all_values_are_unique(self):
        """Every enum value must be unique to avoid aliasing."""
        values = [e.value for e in TrafficLight]
        assert len(values) == len(set(values))

    def test_from_score_returns_green_at_threshold(self):
        """from_score(70) must return GREEN (lower boundary per RN-03)."""
        assert TrafficLight.from_score(70) == TrafficLight.GREEN

    def test_from_score_returns_green_above_threshold(self):
        """from_score(100) must return GREEN."""
        assert TrafficLight.from_score(100) == TrafficLight.GREEN

    def test_from_score_returns_yellow_at_threshold(self):
        """from_score(40) must return YELLOW (lower boundary per RN-03)."""
        assert TrafficLight.from_score(40) == TrafficLight.YELLOW

    def test_from_score_returns_yellow_below_green(self):
        """from_score(69) must return YELLOW (just below GREEN threshold)."""
        assert TrafficLight.from_score(69) == TrafficLight.YELLOW

    def test_from_score_returns_red_just_below_yellow(self):
        """from_score(39) must return RED (just below YELLOW threshold per RN-03)."""
        assert TrafficLight.from_score(39) == TrafficLight.RED

    def test_from_score_returns_red_at_zero(self):
        """from_score(0) must return RED."""
        assert TrafficLight.from_score(0) == TrafficLight.RED
