"""Unit tests for ScoreDTO."""

from app.application.dtos.score_dto import ScoreDTO
from app.domain.value_objects.score import Score


class TestScoreDTO:
    """Tests for ScoreDTO — conversion between domain and application layer."""

    def _make_score(self, **kwargs) -> Score:
        defaults = {
            "expedient_id": "uuid-abc-123",
            "total": 55,
            "detall": {"sector_positiu": 30, "pressupost": 25},
            "paraules_clau_trobades": ("construcció", "obra"),
            "penalitzacions": ("software detectat",),
            "recomanacio": "Viable — puntuació alta",
        }
        defaults.update(kwargs)
        return Score(**defaults)

    # ------------------------------------------------------------------
    # from_domain()
    # ------------------------------------------------------------------

    def test_from_domain_preserves_expedient_id(self):
        """from_domain() must preserve expedient_id."""
        dto = ScoreDTO.from_domain(self._make_score())
        assert dto.expedient_id == "uuid-abc-123"

    def test_from_domain_preserves_total(self):
        """from_domain() must preserve total."""
        dto = ScoreDTO.from_domain(self._make_score(total=30))
        assert dto.total == 30

    def test_from_domain_preserves_detall(self):
        """from_domain() must preserve detall dict."""
        dto = ScoreDTO.from_domain(self._make_score())
        assert dto.detall == {"sector_positiu": 30, "pressupost": 25}

    def test_from_domain_serializes_paraules_clau_as_list(self):
        """from_domain() must convert paraules_clau_trobades tuple to list."""
        dto = ScoreDTO.from_domain(self._make_score())
        assert dto.paraules_clau_trobades == ["construcció", "obra"]

    def test_from_domain_serializes_penalitzacions_as_list(self):
        """from_domain() must convert penalitzacions tuple to list."""
        dto = ScoreDTO.from_domain(self._make_score())
        assert dto.penalitzacions == ["software detectat"]

    def test_from_domain_preserves_recomanacio(self):
        """from_domain() must preserve recomanacio."""
        dto = ScoreDTO.from_domain(self._make_score())
        assert dto.recomanacio == "Viable — puntuació alta"

    def test_from_domain_with_empty_tuples(self):
        """from_domain() must handle empty tuples correctly."""
        score = self._make_score(paraules_clau_trobades=(), penalitzacions=())
        dto = ScoreDTO.from_domain(score)
        assert dto.paraules_clau_trobades == []
        assert dto.penalitzacions == []

    # ------------------------------------------------------------------
    # to_domain()
    # ------------------------------------------------------------------

    def test_to_domain_returns_score_instance(self):
        """to_domain() must return a Score instance."""
        dto = ScoreDTO.from_domain(self._make_score())
        assert isinstance(dto.to_domain(), Score)

    def test_to_domain_converts_paraules_clau_to_tuple(self):
        """to_domain() must convert paraules_clau_trobades list back to tuple."""
        score = self._make_score()
        result = ScoreDTO.from_domain(score).to_domain()
        assert isinstance(result.paraules_clau_trobades, tuple)

    def test_to_domain_converts_penalitzacions_to_tuple(self):
        """to_domain() must convert penalitzacions list back to tuple."""
        score = self._make_score()
        result = ScoreDTO.from_domain(score).to_domain()
        assert isinstance(result.penalitzacions, tuple)

    def test_to_domain_preserves_total(self):
        """to_domain() must preserve total."""
        score = self._make_score(total=10)
        assert ScoreDTO.from_domain(score).to_domain().total == 10

    # ------------------------------------------------------------------
    # Roundtrip
    # ------------------------------------------------------------------

    def test_roundtrip_from_domain_to_domain(self):
        """from_domain() followed by to_domain() must produce an equal Score."""
        score = self._make_score()
        assert ScoreDTO.from_domain(score).to_domain() == score
