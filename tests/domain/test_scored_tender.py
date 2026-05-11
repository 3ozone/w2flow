"""Tests for ScoredTender entity (RF-06, RF-07, RN-03)."""
from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.value_objects.score import Score
from app.domain.value_objects.traffic_light import TrafficLight


def _make_tender() -> Tender:
    """Helper: crea un Tender mínim."""
    return Tender(
        expedient_id="f0b5b0e9-474a-482f-b917-908b85d2ca97",
        publicacio_id=12345,
        organ="Ajuntament de Barcelona",
        titol="Servei de neteja d'oficines",
    )


def _make_scored_tender(total: int) -> ScoredTender:
    """Helper: crea un ScoredTender amb la puntuació indicada."""
    tender = _make_tender()
    score = Score(expedient_id=tender.expedient_id, total=total)
    return ScoredTender(tender=tender, score=score)


def test_is_viable_true():
    """is_viable() ha de retornar True quan score.total >= 40 (RN-03)."""
    scored = _make_scored_tender(total=50)
    assert scored.is_viable() is True


def test_is_viable_false():
    """is_viable() ha de retornar False quan score.total < 40 (RN-03)."""
    scored = _make_scored_tender(total=30)
    assert scored.is_viable() is False


def test_traffic_light():
    """traffic_light() ha de delegar en score.assign_traffic_light() (RN-03)."""
    scored = _make_scored_tender(total=75)
    assert scored.traffic_light() == TrafficLight.GREEN
