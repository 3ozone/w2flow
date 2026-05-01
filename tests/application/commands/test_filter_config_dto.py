"""Unit tests for FilterConfigDTO."""

from app.application.dtos.filter_config_dto import FilterConfigDTO
from app.domain.value_objects.filter_config import FilterConfig


class TestFilterConfigDTO:
    """Tests for FilterConfigDTO — conversion between domain and application layer."""

    def _make_filter_config(self, **kwargs) -> FilterConfig:
        defaults = {
            "tipus_expedient": 1,
            "fase_vigent": 0,
            "sector_keywords": ("construcció", "obra"),
            "max_results": 20,
            "min_pressupost": 50_000.0,
        }
        defaults.update(kwargs)
        return FilterConfig(**defaults)

    # ------------------------------------------------------------------
    # from_domain()
    # ------------------------------------------------------------------

    def test_from_domain_preserves_tipus_expedient(self):
        """from_domain() must preserve tipus_expedient."""
        fc = self._make_filter_config()
        dto = FilterConfigDTO.from_domain(fc)
        assert dto.tipus_expedient == 1

    def test_from_domain_preserves_fase_vigent(self):
        """from_domain() must preserve fase_vigent."""
        fc = self._make_filter_config()
        dto = FilterConfigDTO.from_domain(fc)
        assert dto.fase_vigent == 0

    def test_from_domain_preserves_max_results(self):
        """from_domain() must preserve max_results."""
        fc = self._make_filter_config(max_results=50)
        dto = FilterConfigDTO.from_domain(fc)
        assert dto.max_results == 50

    def test_from_domain_preserves_sector_keywords_as_list(self):
        """from_domain() must convert sector_keywords tuple to list."""
        fc = self._make_filter_config()
        dto = FilterConfigDTO.from_domain(fc)
        assert dto.sector_keywords == ["construcció", "obra"]

    def test_from_domain_preserves_min_pressupost(self):
        """from_domain() must preserve min_pressupost."""
        fc = self._make_filter_config(min_pressupost=100_000.0)
        dto = FilterConfigDTO.from_domain(fc)
        assert dto.min_pressupost == 100_000.0

    # ------------------------------------------------------------------
    # to_domain()
    # ------------------------------------------------------------------

    def test_to_domain_returns_filter_config_instance(self):
        """to_domain() must return a FilterConfig instance."""
        dto = FilterConfigDTO(
            tipus_expedient=1,
            fase_vigent=0,
            max_results=20,
            sector_keywords=["construcció", "obra"],
            min_pressupost=0.0,
        )
        result = dto.to_domain()
        assert isinstance(result, FilterConfig)

    def test_to_domain_preserves_tipus_expedient(self):
        """to_domain() must preserve tipus_expedient."""
        dto = FilterConfigDTO(
            tipus_expedient=2,
            fase_vigent=1,
            max_results=10,
            sector_keywords=["manteniment"],
            min_pressupost=0.0,
        )
        assert dto.to_domain().tipus_expedient == 2

    def test_to_domain_preserves_sector_keywords_as_tuple(self):
        """to_domain() must convert sector_keywords list to tuple."""
        dto = FilterConfigDTO(
            tipus_expedient=1,
            fase_vigent=0,
            max_results=20,
            sector_keywords=["obra", "construcció"],
            min_pressupost=0.0,
        )
        result = dto.to_domain()
        assert result.sector_keywords == ("obra", "construcció")

    # ------------------------------------------------------------------
    # Roundtrip
    # ------------------------------------------------------------------

    def test_roundtrip_from_domain_to_domain(self):
        """from_domain() followed by to_domain() must produce an equal FilterConfig."""
        fc = self._make_filter_config()
        assert FilterConfigDTO.from_domain(fc).to_domain() == fc

    def test_roundtrip_from_dto_to_domain_to_dto(self):
        """to_domain() followed by from_domain() must produce an equal DTO."""
        dto = FilterConfigDTO(
            tipus_expedient=1,
            fase_vigent=0,
            max_results=20,
            sector_keywords=["construcció"],
            min_pressupost=0.0,
        )
        assert FilterConfigDTO.from_domain(dto.to_domain()) == dto
