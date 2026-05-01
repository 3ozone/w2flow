"""Tests for AnalysisService — narrative comparative analysis via Timbal agent."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.value_objects.filter_config import FilterConfig
from app.domain.value_objects.requirements import Requirements
from app.domain.value_objects.score import Score
from app.infrastructure.services.analysis_service import AnalysisService


def _make_scored_tender(expedient_id: str = "uuid-1", total: int = 55) -> ScoredTender:
    tender = Tender(
        expedient_id=expedient_id,
        publicacio_id=42,
        titol="Obres de pavimentació",
        organ="Ajuntament de Girona",
        pressupost=500_000.0,
        codi_expedient="EXP-001",
        fase="0",
        data_publicacio=date.today(),
    )
    score = Score(
        expedient_id=expedient_id,
        total=total,
        detall={
            "pressupost": 20,
            "sector_positiu": 25,
            "sector_negatiu": 0,
            "procediment_obert": 10,
            "subcontractació": 0,
        },
        paraules_clau_trobades=("obres", "pavimentació"),
        penalitzacions=(),
        recomanacio="RECOMANADA",
    )
    requirements = Requirements(
        expedient_id=expedient_id,
        solvency_requirements=(),
        technical_requirements=(),
        adjudication_criteria=(),
        special_clauses=(),
        raw_agent_output="",
    )
    return ScoredTender(tender=tender, score=score, requirements=requirements)


def _mock_agent_on(service: AnalysisService, output_text: str) -> None:
    """Replace the internal Timbal agent with a mock returning output_text."""
    mock_result = MagicMock()
    mock_result.output.collect_text.return_value = output_text
    mock_collect = AsyncMock(return_value=mock_result)
    service._agent = MagicMock(return_value=MagicMock(collect=mock_collect))


class TestAnalysisService:
    """Tests for AnalysisService.analyze()."""

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def test_implements_analysis_port(self):
        """AnalysisService must implement AnalysisPort."""
        from app.application.ports.analysis_port import AnalysisPort
        service = AnalysisService()
        assert isinstance(service, AnalysisPort)

    # ------------------------------------------------------------------
    # Return type
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_returns_string(self):
        """analyze() must return a str."""
        service = AnalysisService()
        _mock_agent_on(service, "Anàlisi comparativa de les licitacions.")
        result = await service.analyze(
            scored_tenders=[_make_scored_tender()],
            pdf_paths=["downloads/uuid-1/PCAP_exp.pdf"],
        )
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_returns_agent_output_text(self):
        """analyze() must return the text produced by the Timbal agent."""
        service = AnalysisService()
        expected = "📋 Obres de pavimentació — Puntuació: 55/70 — RECOMANADA"
        _mock_agent_on(service, expected)
        result = await service.analyze(
            scored_tenders=[_make_scored_tender()],
            pdf_paths=[],
        )
        assert result == expected

    # ------------------------------------------------------------------
    # Agent called
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_calls_agent(self):
        """analyze() must invoke the Timbal agent exactly once."""
        service = AnalysisService()
        mock_result = MagicMock()
        mock_result.output.collect_text.return_value = "output"
        mock_collect = AsyncMock(return_value=mock_result)
        mock_instance = MagicMock(collect=mock_collect)
        mock_agent = MagicMock(return_value=mock_instance)
        service._agent = mock_agent

        await service.analyze(
            scored_tenders=[_make_scored_tender()],
            pdf_paths=[],
        )

        mock_agent.assert_called_once()

    # ------------------------------------------------------------------
    # Graceful degradation
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_returns_empty_string_when_agent_output_is_none(self):
        """analyze() must return empty string when agent output is None."""
        service = AnalysisService()
        mock_result = MagicMock()
        mock_result.output = None
        mock_collect = AsyncMock(return_value=mock_result)
        service._agent = MagicMock(return_value=MagicMock(collect=mock_collect))

        result = await service.analyze(
            scored_tenders=[_make_scored_tender()],
            pdf_paths=[],
        )
        assert result == ""
