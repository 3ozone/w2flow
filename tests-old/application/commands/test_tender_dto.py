"""Unit tests for TenderDTO."""
from datetime import date

from app.application.dtos.tender_dto import TenderDTO
from app.domain.entities.tender import Tender


class TestTenderDTO:
    """Tests for TenderDTO — conversion between domain and application layer."""

    def _make_tender(self, **kwargs) -> Tender:
        defaults = {
            "expedient_id": "uuid-abc-123",
            "publicacio_id": 42,
            "titol": "Obres de construcció de la nova biblioteca",
            "organ": "Ajuntament de Barcelona",
            "pressupost": 250_000.0,
            "codi_expedient": "EXP-2026-001",
            "fase": "0",
            "data_publicacio": date(2026, 4, 30),
        }
        defaults.update(kwargs)
        return Tender(**defaults)

    # ------------------------------------------------------------------
    # from_domain()
    # ------------------------------------------------------------------

    def test_from_domain_preserves_expedient_id(self):
        """from_domain() must preserve expedient_id."""
        dto = TenderDTO.from_domain(self._make_tender())
        assert dto.expedient_id == "uuid-abc-123"

    def test_from_domain_preserves_publicacio_id(self):
        """from_domain() must preserve publicacio_id."""
        dto = TenderDTO.from_domain(self._make_tender())
        assert dto.publicacio_id == 42

    def test_from_domain_preserves_titol(self):
        """from_domain() must preserve titol."""
        dto = TenderDTO.from_domain(self._make_tender())
        assert dto.titol == "Obres de construcció de la nova biblioteca"

    def test_from_domain_preserves_organ(self):
        """from_domain() must preserve organ."""
        dto = TenderDTO.from_domain(self._make_tender())
        assert dto.organ == "Ajuntament de Barcelona"

    def test_from_domain_preserves_pressupost(self):
        """from_domain() must preserve pressupost."""
        dto = TenderDTO.from_domain(self._make_tender())
        assert dto.pressupost == 250_000.0

    def test_from_domain_preserves_codi_expedient(self):
        """from_domain() must preserve codi_expedient."""
        dto = TenderDTO.from_domain(self._make_tender())
        assert dto.codi_expedient == "EXP-2026-001"

    def test_from_domain_serializes_data_publicacio_as_iso_string(self):
        """from_domain() must serialize data_publicacio as ISO 8601 string."""
        dto = TenderDTO.from_domain(self._make_tender())
        assert dto.data_publicacio == "2026-04-30"

    # ------------------------------------------------------------------
    # to_domain()
    # ------------------------------------------------------------------

    def test_to_domain_returns_tender_instance(self):
        """to_domain() must return a Tender instance."""
        dto = TenderDTO.from_domain(self._make_tender())
        assert isinstance(dto.to_domain(), Tender)

    def test_to_domain_preserves_expedient_id(self):
        """to_domain() must preserve expedient_id."""
        tender = self._make_tender()
        assert TenderDTO.from_domain(
            tender).to_domain().expedient_id == tender.expedient_id

    def test_to_domain_parses_data_publicacio_from_string(self):
        """to_domain() must parse data_publicacio ISO string back to date."""
        tender = self._make_tender()
        assert TenderDTO.from_domain(tender).to_domain(
        ).data_publicacio == date(2026, 4, 30)

    # ------------------------------------------------------------------
    # Roundtrip
    # ------------------------------------------------------------------

    def test_roundtrip_from_domain_to_domain(self):
        """from_domain() followed by to_domain() must produce an equal Tender."""
        tender = self._make_tender()
        assert TenderDTO.from_domain(tender).to_domain() == tender
