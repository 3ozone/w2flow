"""Tests for NlpService — requirements extraction via Timbal agent."""

from unittest.mock import AsyncMock, MagicMock
import pytest

from app.domain.value_objects.requirements import Requirements
from app.infrastructure.services.nlp_service import NlpService


def _make_agent_output() -> str:
    return (
        "SOLVENCY_REQUIREMENTS: volum de negoci mínim de 500.000 €\n"
        "TECHNICAL_REQUIREMENTS: experiència prèvia en obres de pavimentació\n"
        "ADJUDICATION_CRITERIA: preu (60%), qualitat tècnica (40%)\n"
        "SPECIAL_CLAUSES: clàusula social de contractació local\n"
    )


class TestNlpServiceExtractRequirements:
    """Tests for NlpService.extract_requirements()."""

    @pytest.mark.asyncio
    async def test_returns_requirements_value_object(self):
        """extract_requirements() must return a Requirements instance."""
        service = NlpService(model="google/gemini-2.5-flash")

        mock_result = MagicMock()
        mock_result.output.collect_text.return_value = _make_agent_output()
        mock_collect = AsyncMock(return_value=mock_result)
        mock_agent = MagicMock(return_value=MagicMock(collect=mock_collect))
        service._agent = mock_agent

        result = await service.extract_requirements(
            expedient_id="uuid-1",
            pdf_texts=["text del PCAP", "text del PPT"],
        )

        assert isinstance(result, Requirements)
        assert result.expedient_id == "uuid-1"

    @pytest.mark.asyncio
    async def test_raw_agent_output_stored(self):
        """extract_requirements() must store the raw LLM response in Requirements."""
        service = NlpService(model="google/gemini-2.5-flash")
        raw_output = _make_agent_output()

        mock_result = MagicMock()
        mock_result.output.collect_text.return_value = raw_output
        mock_collect = AsyncMock(return_value=mock_result)
        mock_agent = MagicMock(return_value=MagicMock(collect=mock_collect))
        service._agent = mock_agent

        result = await service.extract_requirements(
            expedient_id="uuid-1",
            pdf_texts=["text del PCAP"],
        )

        assert result.raw_agent_output == raw_output

    @pytest.mark.asyncio
    async def test_returns_empty_requirements_when_agent_returns_none(self):
        """extract_requirements() must return empty Requirements when agent fails."""
        service = NlpService(model="google/gemini-2.5-flash")

        mock_result = MagicMock()
        mock_result.output = None
        mock_collect = AsyncMock(return_value=mock_result)
        mock_agent = MagicMock(return_value=MagicMock(collect=mock_collect))
        service._agent = mock_agent

        result = await service.extract_requirements(
            expedient_id="uuid-1",
            pdf_texts=["text del PCAP"],
        )

        assert isinstance(result, Requirements)
        assert result.is_empty()

    @pytest.mark.asyncio
    async def test_passes_all_pdf_texts_to_agent(self):
        """extract_requirements() must include all pdf_texts in the agent prompt."""
        service = NlpService(model="google/gemini-2.5-flash")

        mock_result = MagicMock()
        mock_result.output.collect_text.return_value = _make_agent_output()
        mock_collect = AsyncMock(return_value=mock_result)
        mock_agent = MagicMock(return_value=MagicMock(collect=mock_collect))
        service._agent = mock_agent

        await service.extract_requirements(
            expedient_id="uuid-1",
            pdf_texts=["primer pdf", "segon pdf"],
        )

        call_args = mock_agent.call_args
        prompt = call_args.kwargs.get("prompt") or call_args.args[0]
        prompt_str = str(prompt)
        assert "primer pdf" in prompt_str
        assert "segon pdf" in prompt_str
