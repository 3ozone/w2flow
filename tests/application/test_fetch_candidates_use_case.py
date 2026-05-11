"""Tests per a FetchCandidatesUseCase (RF-02, RF-03, RN-01, RN-05, RN-06)."""
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from app.application.use_cases.fetch_candidates_use_case import FetchCandidatesUseCase
from app.domain.entities.tender import Tender
from app.domain.value_objects.filter_config import FilterConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tender(
    expedient_id: str = "exp-001",
    cpv_principal: str = "90910000-9",
    pressupost: float = 50_000.0,
    data_limit: datetime | None = None,
) -> Tender:
    """Crea un Tender mínim per als tests."""
    return Tender(
        expedient_id=expedient_id,
        publicacio_id=1,
        organ="Ajuntament de Test",
        titol="Licitació de test",
        cpv_principal=cpv_principal,
        pressupost=pressupost,
        data_limit=data_limit,
    )


def _make_config(**kwargs) -> FilterConfig:
    """Crea un FilterConfig amb valors per defecte sobreescrivibles."""
    defaults = {"tipus_expedient": 1, "fase_vigent": 0}
    defaults.update(kwargs)
    return FilterConfig(**defaults)


def _make_use_case(tenders: list[Tender], is_duplicate: bool = False):
    """Retorna (use_case, mock_api, mock_repo) amb la API configurada."""
    mock_api = MagicMock()
    mock_api.fetch_tenders.return_value = tenders

    mock_repo = MagicMock()
    mock_repo.is_duplicate.return_value = is_duplicate
    mock_repo.count.return_value = 0

    return FetchCandidatesUseCase(api=mock_api, repository=mock_repo), mock_api, mock_repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFetchCandidatesUseCase:
    """Tests per a FetchCandidatesUseCase."""

    def test_returns_candidates_matching_filter_not_expired_not_duplicate(self):
        """Ha de retornar les licitacions que passen tots els filtres (happy path)."""
        tender = _make_tender()
        config = _make_config(cpv_codes=("90910000-9",))
        use_case, _, _ = _make_use_case(tenders=[tender])

        result = use_case.execute(config=config, today=date(2026, 1, 1))

        assert result == [tender]

    def test_calls_api_with_filter_config_params(self):
        """Ha de cridar l'API amb els paràmetres natius de FilterConfig."""
        tender = _make_tender()
        config = _make_config()
        use_case, mock_api, _ = _make_use_case(tenders=[tender])

        use_case.execute(config=config, today=date(2026, 1, 1))

        mock_api.fetch_tenders.assert_called_once_with(config.to_api_params())

    def test_excludes_tender_not_matching_filter(self):
        """Ha d'excloure les licitacions que no passen el filtre post-fetch."""
        tender = _make_tender(cpv_principal="45000000-7")
        # CPV diferent → no passa
        config = _make_config(cpv_codes=("90910000-9",))
        use_case, _, _ = _make_use_case(tenders=[tender])

        result = use_case.execute(config=config, today=date(2026, 1, 1))

        assert result == []

    def test_excludes_expired_tender(self):
        """Ha d'excloure les licitacions amb data_limit anterior a today (RN-05)."""
        expired = _make_tender(
            data_limit=datetime(2025, 12, 31, tzinfo=timezone.utc)
        )
        config = _make_config()
        use_case, _, _ = _make_use_case(tenders=[expired])

        result = use_case.execute(config=config, today=date(2026, 1, 1))

        assert result == []

    def test_excludes_duplicate_tender(self):
        """Ha d'excloure les licitacions ja processades a la BD (RN-06)."""
        tender = _make_tender()
        config = _make_config()
        use_case, _, _ = _make_use_case(tenders=[tender], is_duplicate=True)

        result = use_case.execute(config=config, today=date(2026, 1, 1))

        assert result == []

    def test_returns_empty_when_api_returns_no_tenders(self):
        """Ha de retornar una llista buida si l'API no retorna resultats."""
        config = _make_config()
        use_case, _, _ = _make_use_case(tenders=[])

        result = use_case.execute(config=config, today=date(2026, 1, 1))

        assert result == []

    def test_filters_and_duplicates_applied_independently(self):
        """Ha d'aplicar filtre, expiració i duplicat de forma independent per cada tender."""
        today = date(2026, 5, 9)
        valid = _make_tender(expedient_id="exp-001",
                             cpv_principal="90910000-9")
        expired = _make_tender(
            expedient_id="exp-002",
            cpv_principal="90910000-9",
            data_limit=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        wrong_cpv = _make_tender(
            expedient_id="exp-003", cpv_principal="45000000-7")

        config = _make_config(cpv_codes=("90910000-9",))

        mock_api = MagicMock()
        mock_api.fetch_tenders.return_value = [valid, expired, wrong_cpv]

        mock_repo = MagicMock()
        mock_repo.is_duplicate.return_value = False

        use_case = FetchCandidatesUseCase(api=mock_api, repository=mock_repo)

        result = use_case.execute(config=config, today=today)

        assert result == [valid]

    def test_starts_on_page_based_on_existing_count(self):
        """Ha de començar a la pàgina count//max_licitacions per saltar les ja processades."""
        tender = _make_tender()
        config = _make_config(max_licitacions=5)

        mock_api = MagicMock()
        mock_api.fetch_tenders.return_value = [tender]

        mock_repo = MagicMock()
        mock_repo.count.return_value = 10  # 10 ja processades → pàgina 2
        mock_repo.is_duplicate.return_value = False

        use_case = FetchCandidatesUseCase(api=mock_api, repository=mock_repo)
        use_case.execute(config=config, today=date(2026, 1, 1))

        called_params = mock_api.fetch_tenders.call_args[0][0]
        assert called_params["page"] == 2  # 10 // 5

    def test_paginates_forward_when_all_results_are_duplicates(self):
        """Ha de demanar la pàgina següent si tots els resultats ja estan a la BD."""
        tender_page0 = _make_tender(expedient_id="exp-dup")
        tender_page1 = _make_tender(expedient_id="exp-new")
        config = _make_config(max_licitacions=1)

        mock_api = MagicMock()
        mock_api.fetch_tenders.side_effect = [[tender_page0], [tender_page1]]

        mock_repo = MagicMock()
        mock_repo.count.return_value = 0
        mock_repo.is_duplicate.side_effect = lambda exp_id: exp_id == "exp-dup"

        use_case = FetchCandidatesUseCase(api=mock_api, repository=mock_repo)
        result = use_case.execute(config=config, today=date(2026, 1, 1))

        assert len(result) == 1
        assert result[0].expedient_id == "exp-new"
        assert mock_api.fetch_tenders.call_count == 2

    def test_stops_paginating_when_api_returns_empty(self):
        """Ha de deixar de paginar si l'API retorna una pàgina buida."""
        config = _make_config(max_licitacions=5)

        mock_api = MagicMock()
        mock_api.fetch_tenders.return_value = []  # cap resultat des del principi

        mock_repo = MagicMock()
        mock_repo.count.return_value = 0
        mock_repo.is_duplicate.return_value = False

        use_case = FetchCandidatesUseCase(api=mock_api, repository=mock_repo)
        result = use_case.execute(config=config, today=date(2026, 1, 1))

        assert result == []
        assert mock_api.fetch_tenders.call_count == 1
