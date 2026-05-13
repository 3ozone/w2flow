"""Tests unitaris per a filters_router — /api/v1/filters.

Verifica el comportament del schema FilterConfigRequest i els endpoints,
incloent valors per defecte i validació de camps.
"""
import pytest
from pydantic import ValidationError

from app.infrastructure.api.filters_router import FilterConfigRequest


# ---------------------------------------------------------------------------
# Tests — FilterConfigRequest schema
# ---------------------------------------------------------------------------

class TestFilterConfigRequestSchema:
    """Tests per al schema Pydantic FilterConfigRequest."""

    def test_camps_obligatoris_valids(self):
        """Crea un FilterConfigRequest amb els camps obligatoris mínims."""
        req = FilterConfigRequest(tipus_expedient=1, fase_vigent=30)

        assert req.tipus_expedient == 1
        assert req.fase_vigent == 30

    def test_fase_vigent_te_valor_per_defecte_30(self):
        """fase_vigent té valor per defecte 30 (ANUNCI_EN_TERMINI) — test RED fins que s'implementi.

        Sense default, el servidor retorna 422 si el formulari no envia fase_vigent.
        El valor 30 correspon a faseVigent=30 (ANUNCI_EN_TERMINI) de l'API real.
        """
        req = FilterConfigRequest(tipus_expedient=1)

        assert req.fase_vigent == 30

    def test_tipus_expedient_es_obligatori(self):
        """Falla si no s'envia tipus_expedient."""
        with pytest.raises(ValidationError):
            FilterConfigRequest()

    def test_classifications_string_json_buida_es_parseja_com_llista_buida(self):
        """classifications: '[]' (string) no ha de produir ["[", "]"] sinó [] (test RED).

        Bug observat: Pydantic v2 en mode lenient itera sobre la string '[]'
        caràcter a caràcter, donant ["[", "]"]. El validator ha de parsejar
        la string JSON com a llista real abans de la validació.
        """
        req = FilterConfigRequest(tipus_expedient=1, classifications="[]")

        assert req.classifications == []

    def test_classifications_string_json_amb_valors_es_parseja_correctament(self):
        """classifications: '["C","G"]' (string) es parseja com ["C", "G"] (test RED)."""
        req = FilterConfigRequest(tipus_expedient=1, classifications='["C","G"]')

        assert req.classifications == ["C", "G"]

    def test_valors_opcionals_tenen_defaults_correctes(self):
        """Camps opcionals retornen els seus valors per defecte."""
        req = FilterConfigRequest(tipus_expedient=1, fase_vigent=30)

        assert req.ambit is None
        assert req.tipus_contracte is None
        assert req.procediment_adjudicacio is None
        assert req.cpv_codes == []
        assert req.pressupost_maxim == 0.0
        assert req.nuts_codes == []
        assert req.classifications == []
        assert req.durada_minima_dies == 0
        assert req.durada_maxima_dies == 0
        assert req.max_licitacions == 20
