"""Unit tests for the FilterConfig value object."""
import pytest

from app.domain.exceptions.filter_validation_error import FilterValidationError
from app.domain.value_objects.filter_config import FilterConfig


class TestFilterConfig:
    """Tests for the FilterConfig value object."""

    # ------------------------------------------------------------------
    # toApiParams()
    # ------------------------------------------------------------------

    def test_to_api_params_contains_tipus_expedient(self):
        """toApiParams() must include tipusExpedient with the configured value."""
        config = FilterConfig(tipus_expedient=1, fase_vigent=0)
        params = config.to_api_params()
        assert params["tipusExpedient"] == 1

    def test_to_api_params_contains_fase_vigent(self):
        """toApiParams() must include faseVigent with the configured value."""
        config = FilterConfig(tipus_expedient=1, fase_vigent=0)
        params = config.to_api_params()
        assert params["faseVigent"] == 0

    def test_to_api_params_contains_size(self):
        """toApiParams() must include a 'size' key to control page size."""
        config = FilterConfig(tipus_expedient=1, fase_vigent=0, max_results=20)
        params = config.to_api_params()
        assert "size" in params

    def test_to_api_params_size_matches_max_results(self):
        """toApiParams() 'size' must equal max_results."""
        config = FilterConfig(tipus_expedient=1, fase_vigent=0, max_results=15)
        assert config.to_api_params()["size"] == 15

    def test_to_api_params_contains_page_zero(self):
        """toApiParams() must include page=0 for the first page."""
        config = FilterConfig(tipus_expedient=1, fase_vigent=0)
        assert config.to_api_params()["page"] == 0

    # ------------------------------------------------------------------
    # matches()
    # ------------------------------------------------------------------

    def test_matches_returns_true_when_pressupost_above_minimum(self):
        """matches() must return True when tender pressupost >= minPressupost."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0, min_pressupost=100_000)
        tender = {"pressupost": 200_000}
        assert config.matches(tender) is True

    def test_matches_returns_true_when_pressupost_equals_minimum(self):
        """matches() must return True when tender pressupost == minPressupost (inclusive)."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0, min_pressupost=100_000)
        tender = {"pressupost": 100_000}
        assert config.matches(tender) is True

    def test_matches_returns_false_when_pressupost_below_minimum(self):
        """matches() must return False when tender pressupost < minPressupost."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0, min_pressupost=100_000)
        tender = {"pressupost": 50_000}
        assert config.matches(tender) is False

    def test_matches_returns_true_when_no_minimum_set(self):
        """matches() must return True for any pressupost when min_pressupost is 0."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0, min_pressupost=0)
        tender = {"pressupost": 1}
        assert config.matches(tender) is True

    def test_matches_returns_false_when_pressupost_is_none(self):
        """matches() must return False when tender pressupost is None and min_pressupost > 0."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0, min_pressupost=100_000)
        tender = {"pressupost": None}
        assert config.matches(tender) is False

    # ------------------------------------------------------------------
    # Equality (frozen dataclass)
    # ------------------------------------------------------------------

    def test_two_configs_with_same_values_are_equal(self):
        """Two FilterConfig instances with identical values must be equal."""
        a = FilterConfig(tipus_expedient=1, fase_vigent=0,
                         min_pressupost=50_000)
        b = FilterConfig(tipus_expedient=1, fase_vigent=0,
                         min_pressupost=50_000)
        assert a == b

    def test_two_configs_with_different_values_are_not_equal(self):
        """Two FilterConfig instances with different values must not be equal."""
        a = FilterConfig(tipus_expedient=1, fase_vigent=0,
                         min_pressupost=50_000)
        b = FilterConfig(tipus_expedient=1, fase_vigent=0,
                         min_pressupost=100_000)
        assert a != b

    def test_config_is_immutable(self):
        """FilterConfig must be immutable (frozen dataclass)."""
        config = FilterConfig(tipus_expedient=1, fase_vigent=0)
        with pytest.raises((AttributeError, TypeError)):
            config.tipus_expedient = 2  # type: ignore[misc]

    # ------------------------------------------------------------------
    # FilterValidationError
    # ------------------------------------------------------------------

    def test_raises_when_tipus_expedient_is_negative(self):
        """FilterValidationError must be raised when tipus_expedient < 0."""
        with pytest.raises(FilterValidationError):
            FilterConfig(tipus_expedient=-1, fase_vigent=0)

    def test_raises_when_fase_vigent_is_negative(self):
        """FilterValidationError must be raised when fase_vigent < 0."""
        with pytest.raises(FilterValidationError):
            FilterConfig(tipus_expedient=1, fase_vigent=-1)

    def test_raises_when_max_results_is_zero(self):
        """FilterValidationError must be raised when max_results <= 0."""
        with pytest.raises(FilterValidationError):
            FilterConfig(tipus_expedient=1, fase_vigent=0, max_results=0)
