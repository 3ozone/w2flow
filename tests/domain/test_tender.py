"""Tests for Tender entity (RF-02, RN-05)."""
from datetime import date, datetime, timezone

from app.domain.entities.tender import Tender


def _make_tender(**kwargs) -> Tender:
    """Helper: crea un Tender mínimo sobreescribiendo solo los campos indicados."""
    defaults = {
        "expedient_id": "f0b5b0e9-474a-482f-b917-908b85d2ca97",
        "publicacio_id": 300688406,
        "organ": "Ajuntament de Montagut i Oix",
        "titol": "Servei de socorrisme piscina 2026",
        "codi_expedient": None,
        "pressupost": None,
        "cpv_principal": None,
        "data_limit": None,
        "durada_dies": None,
        "tipus_contracte_id": None,
        "procediment_id": None,
        "nuts_code": None,
        "classifications": (),
    }
    defaults.update(kwargs)
    return Tender(**defaults)


def test_is_expired_when_deadline_passed():
    """Una licitació amb data límit passada es descarta (RN-05)."""
    tender = _make_tender(
        data_limit=datetime(2026, 5, 7, 23, 59, 59, tzinfo=timezone.utc)
    )
    assert tender.is_expired(today=date(2026, 5, 8)) is True


def test_is_not_expired_when_deadline_future():
    """Una licitació amb data límit futura no es descarta (RN-05)."""
    tender = _make_tender(
        data_limit=datetime(2026, 5, 9, 23, 59, 59, tzinfo=timezone.utc)
    )
    assert tender.is_expired(today=date(2026, 5, 8)) is False


def test_is_not_expired_when_no_deadline():
    """Si no hi ha data límit, la licitació no es descarta per caducitat."""
    tender = _make_tender(data_limit=None)
    assert tender.is_expired(today=date(2026, 5, 8)) is False
