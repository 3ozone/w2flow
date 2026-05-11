"""Tests for TrafficLight value object (RN-03)."""
from app.domain.value_objects.traffic_light import TrafficLight


def test_green():
    """Score >= 70 is GREEN (recommended)."""
    assert TrafficLight.from_score(70) == TrafficLight.GREEN


def test_yellow():
    """Score >= 40 is YELLOW (worth reviewing)."""
    assert TrafficLight.from_score(40) == TrafficLight.YELLOW


def test_red():
    """Score < 40 is RED (not recommended)."""
    assert TrafficLight.from_score(39) == TrafficLight.RED
