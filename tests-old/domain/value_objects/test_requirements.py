"""Unit tests for the Requirements value object."""
import pytest

from app.domain.value_objects.requirements import Requirements


class TestRequirements:
    """Tests for the Requirements value object."""

    def _make_requirements(self, **kwargs) -> Requirements:
        """Helper to build a Requirements instance with sensible defaults."""
        defaults = {
            "expedient_id": "uuid-123",
            "solvency_requirements": ("Solvència econòmica mínima 100.000€",),
            "technical_requirements": ("Experiència en obra civil",),
            "adjudication_criteria": ("Preu: 60pts", "Qualitat: 40pts"),
            "special_clauses": (),
            "raw_agent_output": "Informe complet de l'agent.",
        }
        defaults.update(kwargs)
        return Requirements(**defaults)

    # ------------------------------------------------------------------
    # is_empty()
    # ------------------------------------------------------------------

    def test_is_empty_returns_false_when_all_lists_have_data(self):
        """is_empty() must return False when at least one list has content."""
        req = self._make_requirements()
        assert req.is_empty() is False

    def test_is_empty_returns_true_when_all_lists_are_empty(self):
        """is_empty() must return True when all requirement lists are empty."""
        req = Requirements(
            expedient_id="uuid-empty",
            solvency_requirements=(),
            technical_requirements=(),
            adjudication_criteria=(),
            special_clauses=(),
            raw_agent_output="",
        )
        assert req.is_empty() is True

    def test_is_empty_returns_false_when_only_solvency_has_data(self):
        """is_empty() must return False when only solvency_requirements has content."""
        req = Requirements(
            expedient_id="uuid-partial",
            solvency_requirements=("Solvència econòmica mínima 50.000€",),
            technical_requirements=(),
            adjudication_criteria=(),
            special_clauses=(),
            raw_agent_output="",
        )
        assert req.is_empty() is False

    def test_is_empty_returns_false_when_only_raw_output_has_data(self):
        """is_empty() must return False when raw_agent_output is non-empty."""
        req = Requirements(
            expedient_id="uuid-raw",
            solvency_requirements=(),
            technical_requirements=(),
            adjudication_criteria=(),
            special_clauses=(),
            raw_agent_output="Contingut de l'agent.",
        )
        assert req.is_empty() is False

    # ------------------------------------------------------------------
    # to_dict()
    # ------------------------------------------------------------------

    def test_to_dict_contains_expedient_id(self):
        """to_dict() must include 'expedient_id'."""
        req = self._make_requirements()
        assert req.to_dict()["expedient_id"] == "uuid-123"

    def test_to_dict_contains_solvency_requirements(self):
        """to_dict() must include 'solvency_requirements' as a list."""
        req = self._make_requirements()
        assert "solvency_requirements" in req.to_dict()
        assert isinstance(req.to_dict()["solvency_requirements"], list)

    def test_to_dict_contains_technical_requirements(self):
        """to_dict() must include 'technical_requirements' as a list."""
        req = self._make_requirements()
        assert "technical_requirements" in req.to_dict()

    def test_to_dict_contains_adjudication_criteria(self):
        """to_dict() must include 'adjudication_criteria' as a list."""
        req = self._make_requirements()
        assert "adjudication_criteria" in req.to_dict()

    def test_to_dict_contains_special_clauses(self):
        """to_dict() must include 'special_clauses' as a list."""
        req = self._make_requirements()
        assert "special_clauses" in req.to_dict()

    def test_to_dict_contains_raw_agent_output(self):
        """to_dict() must include 'raw_agent_output'."""
        req = self._make_requirements()
        assert "raw_agent_output" in req.to_dict()

    def test_to_dict_values_match_fields(self):
        """to_dict() values must match the instance fields."""
        req = self._make_requirements()
        d = req.to_dict()
        assert d["solvency_requirements"] == list(req.solvency_requirements)
        assert d["adjudication_criteria"] == list(req.adjudication_criteria)

    # ------------------------------------------------------------------
    # Immutability (frozen dataclass)
    # ------------------------------------------------------------------

    def test_requirements_is_immutable(self):
        """Requirements must be immutable (frozen dataclass)."""
        req = self._make_requirements()
        with pytest.raises((AttributeError, TypeError)):
            req.expedient_id = "other-uuid"  # type: ignore[misc]

    def test_two_requirements_with_same_values_are_equal(self):
        """Two Requirements instances with identical values must be equal."""
        a = self._make_requirements()
        b = self._make_requirements()
        assert a == b

    def test_two_requirements_with_different_values_are_not_equal(self):
        """Two Requirements instances with different values must not be equal."""
        a = self._make_requirements()
        b = self._make_requirements(expedient_id="uuid-456")
        assert a != b
