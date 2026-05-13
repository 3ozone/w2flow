"""Tests for FilterConfig value object (RF-03, RN-07, RN-08, RN-09, RN-10, RN-13, RN-14)."""
import pytest

from app.domain.entities.tender import Tender
from app.domain.exceptions.invalid_filter_config_error import InvalidFilterConfigError
from app.domain.value_objects.filter_config import FilterConfig


def _make_tender(**kwargs) -> Tender:
    """Helper: crea un Tender mínim sobreescrivint els camps indicats."""
    defaults = {
        "expedient_id": "f0b5b0e9-474a-482f-b917-908b85d2ca97",
        "publicacio_id": 12345,
        "organ": "Ajuntament de Barcelona",
        "titol": "Servei de neteja d'oficines",
        "cpv_principal": "90910000-9",
        "pressupost": 100_000.0,
        "nuts_code": "ES511",
        "classifications": ("C",),
    }
    defaults.update(kwargs)
    return Tender(**defaults)


def _make_config(**kwargs) -> FilterConfig:
    """Helper: crea un FilterConfig amb els camps obligatoris i sobreescriu els indicats."""
    defaults = {
        "tipus_expedient": 1,
        "fase_vigent": 0,
    }
    defaults.update(kwargs)
    return FilterConfig(**defaults)


def test_to_api_params():
    """to_api_params() ha d'incloure els filtres natius obligatoris i els opcionals quan tenen valor."""
    config = _make_config(
        tipus_expedient=2,
        fase_vigent=1,
        ambit=3,
        tipus_contracte=1,
        procediment_adjudicacio=2,
    )
    params = config.to_api_params()
    assert params["tipusExpedient"] == 2
    assert params["faseVigent"] == 1
    assert params["ambit"] == 3
    assert params["tipusContracte"] == 1
    assert params["procedimentAdjudicacio"] == 2


def test_to_api_params_omits_none_optionals():
    """to_api_params() no ha d'incloure ambit, tipusContracte ni procedimentAdjudicacio si són None."""
    config = _make_config(ambit=None, tipus_contracte=None,
                          procediment_adjudicacio=None)
    params = config.to_api_params()
    assert "ambit" not in params
    assert "tipusContracte" not in params
    assert "procedimentAdjudicacio" not in params


def test_empty_filters_pass_all():
    """Sense filtres actius (llistes buides, pressupost_maxim=0), qualsevol tender passa (RN-07/08/09/10)."""
    config = _make_config(
        cpv_codes=(),
        pressupost_maxim=0.0,
        nuts_codes=(),
        classifications=(),
    )
    tender = _make_tender()
    assert config.matches(tender) is True


def test_cpv_not_in_list():
    """CPV del tender no és a la llista configurada → False (RN-07)."""
    config = _make_config(cpv_codes=("45000000-7",))
    tender = _make_tender(cpv_principal="90910000-9")
    assert config.matches(tender) is False


def test_pressupost_exceeds_max():
    """Pressupost del tender supera el màxim configurat → False (RN-08)."""
    config = _make_config(pressupost_maxim=500_000.0)
    tender = _make_tender(pressupost=600_000.0)
    assert config.matches(tender) is False


def test_nuts_not_in_list():
    """NUTS del tender no és a la llista configurada → False (RN-09)."""
    config = _make_config(nuts_codes=("ES511",))
    tender = _make_tender(nuts_code="ES700")
    assert config.matches(tender) is False


def test_classification_not_allowed():
    """El tender exigeix un grup que no està a la llista configurada → False (RN-10)."""
    config = _make_config(classifications=("C",))
    tender = _make_tender(classifications=("C", "G"))
    assert config.matches(tender) is False


# ------------------------------------------------------------------
# matches() — durada (RN-11)
# ------------------------------------------------------------------

def test_durada_below_min():
    """Durada del tender és inferior al mínim configurat → False (RN-11)."""
    config = _make_config(durada_minima_dies=90)
    tender = _make_tender(durada_dies=30)
    assert config.matches(tender) is False


def test_durada_exceeds_max():
    """Durada del tender supera el màxim configurat → False (RN-11)."""
    config = _make_config(durada_maxima_dies=180)
    tender = _make_tender(durada_dies=365)
    assert config.matches(tender) is False


# ------------------------------------------------------------------
# max_licitacions (RN-13)
# ------------------------------------------------------------------

def test_max_licitacions_default():
    """max_licitacions té el valor per defecte 20 (RN-13)."""
    config = _make_config()
    assert config.max_licitacions == 20


def test_to_api_params_uses_max_licitacions():
    """to_api_params() ha d'usar max_licitacions com a paràmetre size (RN-13)."""
    config = _make_config(max_licitacions=50)
    params = config.to_api_params()
    assert params["size"] == 50


def test_max_licitacions_minimum_valid():
    """max_licitacions=1 és vàlid (valor mínim, RN-13)."""
    config = _make_config(max_licitacions=1)
    assert config.max_licitacions == 1


def test_max_licitacions_maximum_valid():
    """max_licitacions=100 és vàlid (valor màxim, RN-13)."""
    config = _make_config(max_licitacions=100)
    assert config.max_licitacions == 100


def test_max_licitacions_below_minimum_raises():
    """max_licitacions < 1 ha de llançar InvalidFilterConfigError (RN-13)."""
    with pytest.raises(InvalidFilterConfigError):
        _make_config(max_licitacions=0)


def test_max_licitacions_above_maximum_raises():
    """max_licitacions > 100 ha de llançar InvalidFilterConfigError (RN-13)."""
    with pytest.raises(InvalidFilterConfigError):
        _make_config(max_licitacions=101)


# ------------------------------------------------------------------
# Valors per defecte correctes (RN-14)
# ------------------------------------------------------------------

def test_default_fase_vigent():
    """fase_vigent per defecte ha de ser 30 (Anunci de licitació en termini, RN-14)."""
    config = FilterConfig(tipus_expedient=1)
    assert config.fase_vigent == 30


def test_default_ambit():
    """ambit per defecte ha de ser 1500001 (Generalitat de Catalunya, RN-14)."""
    config = FilterConfig(tipus_expedient=1)
    assert config.ambit == 1500001


def test_default_tipus_contracte():
    """tipus_contracte per defecte ha de ser 395 (Obres, RN-14)."""
    config = FilterConfig(tipus_expedient=1)
    assert config.tipus_contracte == 395


def test_default_procediment_adjudicacio():
    """procediment_adjudicacio per defecte ha de ser 401 (Obert, RN-14)."""
    config = FilterConfig(tipus_expedient=1)
    assert config.procediment_adjudicacio == 401


def test_to_api_params_includes_defaults():
    """to_api_params() ha d'incloure ambit, tipusContracte i procedimentAdjudicacio amb els valors per defecte (RN-14)."""
    config = FilterConfig(tipus_expedient=1)
    params = config.to_api_params()
    assert params["faseVigent"] == 30
    assert params["ambit"] == 1500001
    assert params["tipusContracte"] == 395
    assert params["procedimentAdjudicacio"] == 401
