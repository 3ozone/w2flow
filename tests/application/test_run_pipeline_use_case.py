"""Tests per a RunPipelineUseCase (RF-04, RF-05, RF-06, RF-07)."""
from datetime import date
from unittest.mock import MagicMock

from app.application.dtos.report_dto import ReportDTO
from app.application.dtos.scored_tender_dto import ScoredTenderDTO
from app.application.ports.tender_repository_port import TenderRepositoryPort
from app.application.use_cases.run_pipeline_use_case import RunPipelineUseCase
from app.domain.entities.document import Document
from app.domain.entities.document_analysis import DocumentAnalysis
from app.domain.entities.tender import Tender
from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.filter_config import FilterConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tender(expedient_id: str = "exp-001") -> Tender:
    """Crea un Tender mínim per als tests."""
    return Tender(
        expedient_id=expedient_id,
        publicacio_id=1,
        organ="Ajuntament de Test",
        titol="Licitació de test",
        pressupost=50_000.0,
    )


def _make_document(expedient_id: str = "exp-001") -> Document:
    """Crea un Document obligatori (PCAP) per als tests."""
    return Document(
        expedient_id=expedient_id,
        doc_id=101,
        titol="Plec de clàusules administratives",
        hash="abc123",
        mida=1024,
        doc_type=DocumentType.PCAP,
    )


def _make_analysis(expedient_id: str = "exp-001") -> DocumentAnalysis:
    """Crea un DocumentAnalysis amb puntuació total 75 (semàfor verd)."""
    return DocumentAnalysis(
        expedient_id=expedient_id,
        solvencia=25,
        criteris_adjudicacio=20,
        clausules_atipiques=15,
        procediment=10,
        condicions_execucio=5,
    )


def _make_config() -> FilterConfig:
    """Crea un FilterConfig mínim per als tests."""
    return FilterConfig(tipus_expedient=1, fase_vigent=0)


def _make_use_case(
    candidates: list[Tender],
    documents: list[Document],
    analysis: DocumentAnalysis,
    pdf_bytes: bytes = b"pdf-content",
):
    """Retorna (use_case, mock_fetch, mock_api, mock_nlp, mock_repository) configurats."""
    mock_fetch = MagicMock()
    mock_fetch.execute.return_value = candidates

    mock_api = MagicMock()
    mock_api.fetch_documents.return_value = documents
    mock_api.download_document.return_value = pdf_bytes

    mock_nlp = MagicMock()
    mock_nlp.analyse.return_value = analysis

    mock_repository = MagicMock(spec=TenderRepositoryPort)

    use_case = RunPipelineUseCase(
        fetch_candidates=mock_fetch,
        api=mock_api,
        nlp=mock_nlp,
        repository=mock_repository,
    )
    return use_case, mock_fetch, mock_api, mock_nlp, mock_repository


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRunPipelineUseCase:
    """Tests per a RunPipelineUseCase."""

    def test_returns_report_dto_with_one_scored_tender(self):
        """Ha de retornar un ReportDTO amb un ScoredTenderDTO per cada candidat."""
        tender = _make_tender()
        document = _make_document()
        analysis = _make_analysis()
        config = _make_config()
        use_case, _, _, _, _ = _make_use_case([tender], [document], analysis)

        result = use_case.execute(config=config, today=date(2026, 5, 9))

        assert isinstance(result, ReportDTO)
        assert len(result.tenders) == 1
        assert isinstance(result.tenders[0], ScoredTenderDTO)

    def test_scored_tender_dto_has_correct_fields(self):
        """El ScoredTenderDTO ha de contenir els camps correctes de la licitació."""
        tender = _make_tender()
        analysis = _make_analysis()
        config = _make_config()
        use_case, _, _, _, _ = _make_use_case([tender], [_make_document()], analysis)

        result = use_case.execute(config=config, today=date(2026, 5, 9))

        dto = result.tenders[0]
        assert dto.expedient_id == "exp-001"
        assert dto.titol == "Licitació de test"
        assert dto.organ == "Ajuntament de Test"
        assert dto.pressupost == 50_000.0
        assert dto.total == 75
        assert dto.traffic_light == "green"

    def test_report_counts_are_correct(self):
        """El ReportDTO ha de tenir total_candidates i total_viable correctes."""
        tender = _make_tender()
        analysis = _make_analysis()  # total=75 → viable
        config = _make_config()
        use_case, _, _, _, _ = _make_use_case([tender], [_make_document()], analysis)

        result = use_case.execute(config=config, today=date(2026, 5, 9))

        assert result.total_candidates == 1
        assert result.total_viable == 1

    def test_only_mandatory_documents_are_downloaded(self):
        """Només els documents obligatoris (PCAP, PPT, TECHNICAL_MEMORY) s'han de descarregar."""
        tender = _make_tender()
        mandatory = _make_document()  # PCAP → obligatori
        optional = Document(
            expedient_id="exp-001",
            doc_id=202,
            titol="Annex",
            hash="def456",
            mida=512,
            doc_type=DocumentType.UNKNOWN,
        )
        analysis = _make_analysis()
        config = _make_config()
        use_case, _, mock_api, _, _ = _make_use_case(
            [tender], [mandatory, optional], analysis
        )

        use_case.execute(config=config, today=date(2026, 5, 9))

        # Només s'ha cridat download_document per al document obligatori
        mock_api.download_document.assert_called_once_with(
            mandatory.doc_id, mandatory.hash
        )

    def test_calls_fetch_candidates_with_config_and_today(self):
        """Ha de delegar la cerca de candidats a FetchCandidatesUseCase."""
        tender = _make_tender()
        config = _make_config()
        today = date(2026, 5, 9)
        use_case, mock_fetch, _, _, _ = _make_use_case(
            [tender], [_make_document()], _make_analysis()
        )

        use_case.execute(config=config, today=today)

        mock_fetch.execute.assert_called_once_with(config=config, today=today)

    def test_calls_nlp_with_mandatory_pdf_bytes(self):
        """Ha de cridar NlpAnalyserPort.analyse amb l'expedient_id i els bytes dels PDFs."""
        tender = _make_tender()
        document = _make_document()
        analysis = _make_analysis()
        config = _make_config()
        pdf_bytes = b"pdf-content"
        use_case, _, _, mock_nlp, _ = _make_use_case(
            [tender], [document], analysis, pdf_bytes=pdf_bytes
        )

        use_case.execute(config=config, today=date(2026, 5, 9))

        mock_nlp.analyse.assert_called_once_with(
            expedient_id="exp-001", documents=[pdf_bytes]
        )

    def test_returns_empty_report_when_no_candidates(self):
        """Ha de retornar un ReportDTO buit si no hi ha candidats."""
        config = _make_config()
        use_case, _, _, _, _ = _make_use_case([], [], _make_analysis())

        result = use_case.execute(config=config, today=date(2026, 5, 9))

        assert result == ReportDTO()

    def test_non_viable_tender_counted_but_not_viable(self):
        """Una licitació amb puntuació < 40 ha de comptar com a candidat però no com a viable."""
        tender = _make_tender()
        low_analysis = DocumentAnalysis(
            expedient_id="exp-001",
            solvencia=5,
            criteris_adjudicacio=5,
            clausules_atipiques=5,
            procediment=5,
            condicions_execucio=5,
        )  # total=25 → no viable
        config = _make_config()
        use_case, _, _, _, _ = _make_use_case(
            [tender], [_make_document()], low_analysis
        )

        result = use_case.execute(config=config, today=date(2026, 5, 9))

        assert result.total_candidates == 1
        assert result.total_viable == 0
        assert result.tenders[0].traffic_light == "red"

    def test_saves_each_tender_to_repository(self):
        """Ha de cridar repository.save() per a cada licitació processada."""
        tender1 = _make_tender(expedient_id="exp-001")
        tender2 = _make_tender(expedient_id="exp-002")
        tender2.publicacio_id = 2
        config = _make_config()
        use_case, _, _, _, mock_repository = _make_use_case(
            [tender1, tender2], [_make_document()], _make_analysis()
        )

        use_case.execute(config=config, today=date(2026, 5, 9))

        assert mock_repository.save.call_count == 2
        saved_ids = {call.args[0].expedient_id for call in mock_repository.save.call_args_list}
        assert saved_ids == {"exp-001", "exp-002"}
