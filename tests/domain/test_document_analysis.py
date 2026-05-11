"""Tests for DocumentAnalysis entity (RF-05, RN-12)."""
import pytest

from app.domain.entities.document_analysis import DocumentAnalysis
from app.domain.exceptions.invalid_score_error import InvalidScoreError


def _make_analysis(**kwargs) -> DocumentAnalysis:
    """Helper: crea un DocumentAnalysis mínim sobreescrivint els camps indicats."""
    defaults = {
        "expedient_id": "f0b5b0e9-474a-482f-b917-908b85d2ca97",
        "solvencia": 20,
        "criteris_adjudicacio": 15,
        "clausules_atipiques": 10,
        "procediment": 10,
        "condicions_execucio": 5,
    }
    defaults.update(kwargs)
    return DocumentAnalysis(**defaults)


def test_to_score_total():
    """to_score() ha de sumar els 5 criteris correctament (RN-12)."""
    analysis = _make_analysis(
        solvencia=20,
        criteris_adjudicacio=15,
        clausules_atipiques=10,
        procediment=10,
        condicions_execucio=5,
    )
    score = analysis.to_score()
    assert score.total == 60


def test_to_score_returns_score_with_expedient_id():
    """to_score() ha de retornar un Score amb el mateix expedient_id."""
    analysis = _make_analysis()
    score = analysis.to_score()
    assert score.expedient_id == analysis.expedient_id


def test_to_score_max_values():
    """Amb tots els valors màxims (30+25+20+15+10), total ha de ser 100 (RN-12)."""
    analysis = _make_analysis(
        solvencia=30,
        criteris_adjudicacio=25,
        clausules_atipiques=20,
        procediment=15,
        condicions_execucio=10,
    )
    score = analysis.to_score()
    assert score.total == 100


# ---------------------------------------------------------------------------
# Validació de rangs (InvalidScoreError)
# ---------------------------------------------------------------------------

def test_raises_if_solvencia_negative():
    """Ha de llançar InvalidScoreError si solvencia < 0."""
    with pytest.raises(InvalidScoreError):
        _make_analysis(solvencia=-1)


def test_raises_if_solvencia_exceeds_max():
    """Ha de llançar InvalidScoreError si solvencia > 30."""
    with pytest.raises(InvalidScoreError):
        _make_analysis(solvencia=31)


def test_raises_if_criteris_adjudicacio_exceeds_max():
    """Ha de llançar InvalidScoreError si criteris_adjudicacio > 25."""
    with pytest.raises(InvalidScoreError):
        _make_analysis(criteris_adjudicacio=26)


def test_raises_if_clausules_atipiques_exceeds_max():
    """Ha de llançar InvalidScoreError si clausules_atipiques > 20."""
    with pytest.raises(InvalidScoreError):
        _make_analysis(clausules_atipiques=21)


def test_raises_if_procediment_exceeds_max():
    """Ha de llançar InvalidScoreError si procediment > 15."""
    with pytest.raises(InvalidScoreError):
        _make_analysis(procediment=16)


def test_raises_if_condicions_execucio_exceeds_max():
    """Ha de llançar InvalidScoreError si condicions_execucio > 10."""
    with pytest.raises(InvalidScoreError):
        _make_analysis(condicions_execucio=11)


def test_does_not_raise_with_all_zeros():
    """Ha d'acceptar tots els criteris a 0 (puntuació mínima vàlida)."""
    analysis = _make_analysis(
        solvencia=0,
        criteris_adjudicacio=0,
        clausules_atipiques=0,
        procediment=0,
        condicions_execucio=0,
    )
    assert analysis.to_score().total == 0
