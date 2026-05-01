"""Tests for Pydantic API schemas — FilterSchema validation."""

import pytest
from pydantic import ValidationError

from app.infrastructure.api.v1.schemas.filter_schema import FilterSchema
from app.domain.value_objects.filter_config import FilterConfig


class TestFilterSchemaValidation:
    """Tests for FilterSchema field validation."""

    def test_valid_payload_creates_schema(self):
        """A valid payload must be accepted without errors."""
        schema = FilterSchema(
            tipus_expedient=1,
            fase_vigent=0,
            max_results=20,
            sector_keywords=["construcció", "obra civil"],
            min_pressupost=100_000.0,
        )
        assert schema.tipus_expedient == 1
        assert schema.fase_vigent == 0

    def test_missing_required_fields_raises_validation_error(self):
        """tipus_expedient and fase_vigent are required — omitting them must fail."""
        with pytest.raises(ValidationError):
            FilterSchema()

    def test_negative_tipus_expedient_raises_validation_error(self):
        """tipus_expedient must be >= 0."""
        with pytest.raises(ValidationError):
            FilterSchema(tipus_expedient=-1, fase_vigent=0)

    def test_negative_fase_vigent_raises_validation_error(self):
        """fase_vigent must be >= 0."""
        with pytest.raises(ValidationError):
            FilterSchema(tipus_expedient=1, fase_vigent=-1)

    def test_negative_min_pressupost_raises_validation_error(self):
        """min_pressupost must be >= 0."""
        with pytest.raises(ValidationError):
            FilterSchema(tipus_expedient=1, fase_vigent=0, min_pressupost=-1.0)

    def test_max_results_below_one_raises_validation_error(self):
        """max_results must be >= 1."""
        with pytest.raises(ValidationError):
            FilterSchema(tipus_expedient=1, fase_vigent=0, max_results=0)

    def test_defaults_applied_when_optional_fields_omitted(self):
        """Optional fields must use their defaults when not provided."""
        schema = FilterSchema(tipus_expedient=1, fase_vigent=0)
        assert schema.max_results == 20
        assert schema.sector_keywords == []
        assert schema.min_pressupost == 0.0

    def test_to_domain_returns_filter_config(self):
        """to_domain() must return a FilterConfig value object."""
        schema = FilterSchema(
            tipus_expedient=1,
            fase_vigent=0,
            sector_keywords=["obra civil"],
            min_pressupost=50_000.0,
        )
        domain = schema.to_domain()
        assert isinstance(domain, FilterConfig)
        assert domain.tipus_expedient == 1
        assert domain.fase_vigent == 0
        assert "obra civil" in domain.sector_keywords
        assert domain.min_pressupost == 50_000.0
