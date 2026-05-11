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
    # matches() — sector_keywords (RF-03)
    # ------------------------------------------------------------------

    def test_matches_returns_true_with_positive_keyword_in_titol(self):
        """matches() must return True when tender titol contains a positive sector keyword."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0,
            sector_keywords=("construcció",),
        )
        tender = {"pressupost": 100_000,
                  "titol": "Obres de construcció del carrer"}
        assert config.matches(tender) is True

    def test_matches_returns_true_without_keyword_in_titol(self):
        """matches() must return True even when titol has no keyword — keywords are bonus, not mandatory."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0,
            sector_keywords=("construcció",),
        )
        tender = {"pressupost": 100_000,
                  "titol": "Servei de neteja d'oficines"}
        assert config.matches(tender) is True

    def test_matches_returns_false_with_negative_keyword_in_titol(self):
        """matches() must discard a tender whose titol contains a negative keyword (prefixed with -)."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0,
            sector_keywords=("-software", "-saas"),
        )
        tender = {"pressupost": 100_000, "titol": "Plataforma de software ERP"}
        assert config.matches(tender) is False

    def test_matches_returns_true_when_no_sector_keywords_configured(self):
        """matches() must pass all tenders when sector_keywords is empty."""
        config = FilterConfig(tipus_expedient=1, fase_vigent=0)
        tender = {"pressupost": 100_000, "titol": "Qualsevol licitació"}
        assert config.matches(tender) is True

    # ------------------------------------------------------------------
    # matches() — cpv_codes (Fase 12.1, RN-07)
    # ------------------------------------------------------------------

    def test_matches_passes_when_cpv_codes_empty(self):
        """matches() must pass any tender when cpv_codes is empty (no CPV filter)."""
        config = FilterConfig(tipus_expedient=1, fase_vigent=0)
        tender = {"pressupost": 100_000, "codi_cpv": "45000000-7"}
        assert config.matches(tender) is True

    def test_matches_passes_when_cpv_in_list(self):
        """matches() must pass a tender whose codi_cpv is in cpv_codes."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0,
            cpv_codes=("45000000-7", "71000000-8"),
        )
        tender = {"pressupost": 100_000, "codi_cpv": "45000000-7"}
        assert config.matches(tender) is True

    def test_matches_discards_when_cpv_not_in_list(self):
        """matches() must discard a tender whose codi_cpv is not in cpv_codes."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0,
            cpv_codes=("45000000-7",),
        )
        tender = {"pressupost": 100_000, "codi_cpv": "72000000-5"}
        assert config.matches(tender) is False

    def test_matches_discards_when_cpv_is_none_and_filter_active(self):
        """matches() must discard a tender with no CPV when cpv_codes filter is active."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0,
            cpv_codes=("45000000-7",),
        )
        tender = {"pressupost": 100_000, "codi_cpv": None}
        assert config.matches(tender) is False

    def test_matches_passes_when_cpv_is_none_and_no_filter(self):
        """matches() must pass a tender with no CPV when cpv_codes is empty."""
        config = FilterConfig(tipus_expedient=1, fase_vigent=0)
        tender = {"pressupost": 100_000, "codi_cpv": None}
        assert config.matches(tender) is True

    # ------------------------------------------------------------------
    # matches() — max_pressupost (Fase 12.2, RN-08)
    # ------------------------------------------------------------------

    def test_matches_passes_when_max_pressupost_is_zero(self):
        """matches() must pass any tender when max_pressupost is 0 (no upper limit)."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0, max_pressupost=0.0)
        tender = {"pressupost": 99_000_000}
        assert config.matches(tender) is True

    def test_matches_passes_when_pressupost_below_max(self):
        """matches() must pass a tender whose pressupost is below max_pressupost."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0, max_pressupost=500_000.0)
        tender = {"pressupost": 400_000}
        assert config.matches(tender) is True

    def test_matches_passes_when_pressupost_equals_max(self):
        """matches() must pass a tender whose pressupost equals max_pressupost (inclusive)."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0, max_pressupost=500_000.0)
        tender = {"pressupost": 500_000}
        assert config.matches(tender) is True

    def test_matches_discards_when_pressupost_exceeds_max(self):
        """matches() must discard a tender whose pressupost exceeds max_pressupost."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0, max_pressupost=500_000.0)
        tender = {"pressupost": 600_000}
        assert config.matches(tender) is False

    def test_matches_passes_when_pressupost_none_and_max_active(self):
        """matches() must pass a tender with pressupost=None when max_pressupost is set (no data = no discard)."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0, max_pressupost=500_000.0)
        tender = {"pressupost": None}
        assert config.matches(tender) is True

    def test_matches_returns_true_when_negative_keyword_not_present(self):
        """matches() must pass a tender that does NOT contain the negative keyword."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0,
            sector_keywords=("-software",),
        )
        tender = {"pressupost": 100_000, "titol": "Obres de rehabilitació"}
        assert config.matches(tender) is True

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

    # ------------------------------------------------------------------
    # exclude_alerta_futura
    # ------------------------------------------------------------------

    def test_matches_discards_alerta_futura_when_excluded(self):
        """matches() must return False for ALERTA_FUTURA when exclude_alerta_futura=True."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0, exclude_alerta_futura=True)
        assert config.matches(
            {"pressupost": 100_000, "fase": "ALERTA_FUTURA"}) is False

    def test_matches_accepts_alerta_futura_when_not_excluded(self):
        """matches() must return True for ALERTA_FUTURA when exclude_alerta_futura=False."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0, exclude_alerta_futura=False)
        assert config.matches(
            {"pressupost": 100_000, "fase": "ALERTA_FUTURA"}) is True

    def test_matches_accepts_anunci_licitacio_when_excluded(self):
        """matches() must return True for ANUNCI_LICITACIO regardless of exclude_alerta_futura."""
        config = FilterConfig(
            tipus_expedient=1, fase_vigent=0, exclude_alerta_futura=True)
        assert config.matches(
            {"pressupost": 100_000, "fase": "ANUNCI_LICITACIO"}) is True

    def test_exclude_alerta_futura_defaults_to_true(self):
        """exclude_alerta_futura must default to True."""
        config = FilterConfig(tipus_expedient=1, fase_vigent=0)
        assert config.exclude_alerta_futura is True
