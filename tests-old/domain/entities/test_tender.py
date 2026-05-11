"""Unit tests for the Tender entity."""
import pytest
from datetime import date, timedelta

from app.domain.entities.tender import Tender
from app.domain.exceptions.expired_tender_error import ExpiredTenderError


class TestTender:
    """Tests for the Tender entity."""

    def _make_tender(self, **kwargs) -> Tender:
        """Helper to build a Tender instance with sensible defaults."""
        defaults = {
            "expedient_id": "uuid-abc-123",
            "publicacio_id": 42,
            "titol": "Obres de construcció de la nova biblioteca",
            "organ": "Ajuntament de Barcelona",
            "pressupost": 250_000.0,
            "codi_expedient": "EXP-2026-001",
            "fase": "0",
            "data_publicacio": date.today(),
        }
        defaults.update(kwargs)
        return Tender(**defaults)

    # ------------------------------------------------------------------
    # is_new()
    # ------------------------------------------------------------------

    def test_is_new_returns_true_for_today(self):
        """is_new() must return True when data_publicacio is today."""
        tender = self._make_tender(data_publicacio=date.today())
        assert tender.is_new() is True

    def test_is_new_returns_false_for_yesterday(self):
        """is_new() must return False when data_publicacio is yesterday."""
        tender = self._make_tender(
            data_publicacio=date.today() - timedelta(days=1))
        assert tender.is_new() is False

    def test_is_new_returns_false_for_old_date(self):
        """is_new() must return False for a date older than today."""
        tender = self._make_tender(data_publicacio=date(2025, 1, 1))
        assert tender.is_new() is False

    # ------------------------------------------------------------------
    # get_basic_info()
    # ------------------------------------------------------------------

    def test_get_basic_info_contains_expedient_id(self):
        """get_basic_info() must include 'expedient_id'."""
        tender = self._make_tender()
        info = tender.get_basic_info()
        assert info["expedient_id"] == "uuid-abc-123"

    def test_get_basic_info_contains_titol(self):
        """get_basic_info() must include 'titol'."""
        tender = self._make_tender()
        assert "titol" in tender.get_basic_info()

    def test_get_basic_info_contains_organ(self):
        """get_basic_info() must include 'organ'."""
        tender = self._make_tender()
        assert "organ" in tender.get_basic_info()

    def test_get_basic_info_contains_pressupost(self):
        """get_basic_info() must include 'pressupost'."""
        tender = self._make_tender()
        assert "pressupost" in tender.get_basic_info()

    def test_get_basic_info_contains_codi_expedient(self):
        """get_basic_info() must include 'codi_expedient'."""
        tender = self._make_tender()
        assert "codi_expedient" in tender.get_basic_info()

    # ------------------------------------------------------------------
    # Equality by expedient_id
    # ------------------------------------------------------------------

    def test_equality_by_expedient_id_same(self):
        """Two Tender instances with the same expedient_id must be equal."""
        a = self._make_tender()
        b = self._make_tender(titol="Títol diferent", organ="Altre organ")
        assert a == b

    def test_equality_by_expedient_id_different(self):
        """Two Tender instances with different expedient_id must not be equal."""
        a = self._make_tender(expedient_id="uuid-aaa")
        b = self._make_tender(expedient_id="uuid-bbb")
        assert a != b

    def test_hash_by_expedient_id(self):
        """Two Tenders with the same expedient_id must have the same hash."""
        a = self._make_tender()
        b = self._make_tender(titol="Títol diferent")
        assert hash(a) == hash(b)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_empty_expedient_id_raises(self):
        """Tender must raise ValueError if expedient_id is empty."""
        with pytest.raises(ValueError):
            self._make_tender(expedient_id="")

    def test_empty_titol_raises(self):
        """Tender must raise ValueError if titol is empty."""
        with pytest.raises(ValueError):
            self._make_tender(titol="")

    def test_negative_pressupost_raises(self):
        """Tender must raise ValueError if pressupost is negative."""
        with pytest.raises(ValueError):
            self._make_tender(pressupost=-1.0)

    def test_pressupost_none_is_allowed(self):
        """Tender must accept pressupost=None when budget is not published."""
        tender = self._make_tender(pressupost=None)
        assert tender.pressupost is None

    # ------------------------------------------------------------------
    # Fase 11.4 — Optional fields: codi_cpv, termini_execucio, data_limit_presentacio
    # ------------------------------------------------------------------

    def test_codi_cpv_defaults_to_none(self):
        """codi_cpv must default to None when not provided."""
        tender = self._make_tender()
        assert tender.codi_cpv is None

    def test_codi_cpv_can_be_set(self):
        """codi_cpv must accept a CPV code string."""
        tender = self._make_tender(codi_cpv="45233000-9")
        assert tender.codi_cpv == "45233000-9"

    def test_termini_execucio_defaults_to_none(self):
        """termini_execucio must default to None when not provided."""
        tender = self._make_tender()
        assert tender.termini_execucio is None

    def test_termini_execucio_can_be_set(self):
        """termini_execucio must accept a string value."""
        tender = self._make_tender(termini_execucio="12 mesos")
        assert tender.termini_execucio == "12 mesos"

    def test_data_limit_presentacio_defaults_to_none(self):
        """data_limit_presentacio must default to None when not provided."""
        tender = self._make_tender()
        assert tender.data_limit_presentacio is None

    def test_data_limit_presentacio_can_be_set(self):
        """data_limit_presentacio must accept a string value."""
        tender = self._make_tender(data_limit_presentacio="2026-06-15")
        assert tender.data_limit_presentacio == "2026-06-15"

    def test_tender_without_optional_fields_is_valid(self):
        """A Tender without optional fields (all None) must be valid."""
        tender = self._make_tender(
            codi_cpv=None,
            termini_execucio=None,
            data_limit_presentacio=None,
        )
        assert tender.expedient_id == "uuid-abc-123"
        assert tender.codi_cpv is None
        assert tender.termini_execucio is None
        assert tender.data_limit_presentacio is None

    def test_pressupost_none_does_not_raise_negative_validation(self):
        """Negative pressupost validation must not apply when pressupost is None."""
        # Should not raise
        tender = self._make_tender(pressupost=None)
        assert tender.pressupost is None
