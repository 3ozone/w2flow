"""Tests for ComparativeReport entity (RF-07, RN-03)."""
from app.domain.entities.comparative_report import ComparativeReport
from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.value_objects.score import Score


def _make_scored_tender(expedient_id: str, total: int) -> ScoredTender:
    """Helper: crea un ScoredTender amb la puntuació indicada."""
    tender = Tender(
        expedient_id=expedient_id,
        publicacio_id=1,
        organ="Ajuntament de Barcelona",
        titol="Licitació de prova",
    )
    score = Score(expedient_id=expedient_id, total=total)
    return ScoredTender(tender=tender, score=score)


def test_get_viable_tenders_returns_only_viable():
    """get_viable_tenders() ha de retornar només els ScoredTender amb total >= 40 (RN-03)."""
    viable = _make_scored_tender("id-1", total=70)
    not_viable = _make_scored_tender("id-2", total=30)
    report = ComparativeReport(tenders=[viable, not_viable])
    result = report.get_viable_tenders()
    assert result == [viable]


def test_get_viable_tenders_empty_when_none_viable():
    """get_viable_tenders() ha de retornar llista buida si cap tender és viable (RN-03)."""
    report = ComparativeReport(tenders=[
        _make_scored_tender("id-1", total=20),
        _make_scored_tender("id-2", total=10),
    ])
    assert report.get_viable_tenders() == []
