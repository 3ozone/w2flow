"""Tests for ScoreTenderCommandHandler."""

from datetime import date
from unittest.mock import AsyncMock
import pytest

from app.application.use_cases.commands.score_tender_command import (
    ScoreTenderCommand,
    ScoreTenderCommandHandler,
)
from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.value_objects.filter_config import FilterConfig


def _make_tender(
    expedient_id: str = "uuid-1",
    titol: str = "Obres de construcció de la nova biblioteca",
    pressupost: float = 200_000.0,
) -> Tender:
    return Tender(
        expedient_id=expedient_id,
        publicacio_id=1,
        titol=titol,
        organ="Ajuntament de Barcelona",
        pressupost=pressupost,
        codi_expedient=f"EXP-{expedient_id}",
        fase="0",
        data_publicacio=date.today(),
    )


def _make_filter_config(**kwargs) -> FilterConfig:
    defaults = {
        "tipus_expedient": 1,
        "fase_vigent": 0,
        "sector_keywords": ("construcció", "obra"),
    }
    defaults.update(kwargs)
    return FilterConfig(**defaults)


class TestScoreTenderCommandHandler:
    """Tests for ScoreTenderCommandHandler."""

    def _make_handler(self):
        repository = AsyncMock()
        return ScoreTenderCommandHandler(repository=repository), repository

    # ------------------------------------------------------------------
    # Returns ScoredTender
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_returns_scored_tender_instance(self):
        """handle() must return a ScoredTender instance."""
        handler, _ = self._make_handler()
        command = ScoreTenderCommand(
            tender=_make_tender(),
            filter_config=_make_filter_config(),
            pdf_texts=[],
        )
        result = await handler.handle(command)
        assert isinstance(result, ScoredTender)

    @pytest.mark.asyncio
    async def test_scored_tender_has_correct_tender(self):
        """handle() must bind the original tender to the ScoredTender."""
        handler, _ = self._make_handler()
        tender = _make_tender()
        command = ScoreTenderCommand(
            tender=tender,
            filter_config=_make_filter_config(),
            pdf_texts=[],
        )
        result = await handler.handle(command)
        assert result.tender == tender

    # ------------------------------------------------------------------
    # Score calculation — pressupost
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_score_pressupost_above_1M_gets_30pts(self):
        """Pressupost >= 1_000_000 must yield 30 pts from pressupost (RF-06)."""
        handler, _ = self._make_handler()
        command = ScoreTenderCommand(
            tender=_make_tender(pressupost=1_500_000.0),
            filter_config=_make_filter_config(),
            pdf_texts=[],
        )
        result = await handler.handle(command)
        assert result.score.detall["pressupost"] == 30

    @pytest.mark.asyncio
    async def test_score_pressupost_100k_to_500k_gets_15pts(self):
        """Pressupost between 100_000 and 499_999 must yield 15 pts (RF-06)."""
        handler, _ = self._make_handler()
        command = ScoreTenderCommand(
            tender=_make_tender(pressupost=200_000.0),
            filter_config=_make_filter_config(),
            pdf_texts=[],
        )
        result = await handler.handle(command)
        assert result.score.detall["pressupost"] == 15

    @pytest.mark.asyncio
    async def test_score_pressupost_below_100k_gets_5pts(self):
        """Pressupost < 100_000 must yield 5 pts."""
        handler, _ = self._make_handler()
        command = ScoreTenderCommand(
            tender=_make_tender(pressupost=50_000.0),
            filter_config=_make_filter_config(),
            pdf_texts=[],
        )
        result = await handler.handle(command)
        assert result.score.detall["pressupost"] == 5

    # ------------------------------------------------------------------
    # Score calculation — sector keywords
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_sector_keywords_in_title_add_points(self):
        """Keywords matching in tender titol must add sector_positiu points."""
        handler, _ = self._make_handler()
        command = ScoreTenderCommand(
            tender=_make_tender(titol="obres de construcció i rehabilitació"),
            filter_config=_make_filter_config(),
            pdf_texts=[],
        )
        result = await handler.handle(command)
        assert result.score.detall["sector_positiu"] > 0

    @pytest.mark.asyncio
    async def test_negative_keywords_penalize_score(self):
        """IT/software keywords in text must add negative sector_negatiu points."""
        handler, _ = self._make_handler()
        command = ScoreTenderCommand(
            tender=_make_tender(titol="plataforma digital i software"),
            filter_config=_make_filter_config(),
            pdf_texts=["software saas gestió"],
        )
        result = await handler.handle(command)
        assert result.score.detall["sector_negatiu"] < 0

    @pytest.mark.asyncio
    async def test_total_score_does_not_go_below_zero(self):
        """Total score must never be negative."""
        handler, _ = self._make_handler()
        command = ScoreTenderCommand(
            tender=_make_tender(
                titol="software saas plataforma digital", pressupost=1_000.0),
            filter_config=_make_filter_config(),
            pdf_texts=[
                "software saas plataforma digital aplicació web recursos humans"],
        )
        result = await handler.handle(command)
        assert result.score.total >= 0

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_saves_scored_tender_to_repository(self):
        """handle() must call repository.save_scored() with the result."""
        handler, repository = self._make_handler()
        command = ScoreTenderCommand(
            tender=_make_tender(),
            filter_config=_make_filter_config(),
            pdf_texts=[],
        )
        result = await handler.handle(command)
        repository.save_scored.assert_called_once_with(result)

    # ------------------------------------------------------------------
    # pdf_texts influence scoring
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_pdf_texts_with_positive_keywords_increase_score(self):
        """Keywords found only in pdf_texts (not in titol) must add sector_positiu points."""
        handler, _ = self._make_handler()

        # Titol neutral — no sector keywords
        command_without_pdf = ScoreTenderCommand(
            tender=_make_tender(titol="Contracte de serveis generals"),
            filter_config=_make_filter_config(),
            pdf_texts=[],
        )
        result_without = await handler.handle(command_without_pdf)

        # Same titol, but pdf_texts contain sector keywords
        command_with_pdf = ScoreTenderCommand(
            tender=_make_tender(titol="Contracte de serveis generals"),
            filter_config=_make_filter_config(),
            pdf_texts=["obres de construcció i rehabilitació d'edificació"],
        )
        result_with = await handler.handle(command_with_pdf)

        assert result_with.score.total > result_without.score.total

    @pytest.mark.asyncio
    async def test_pdf_texts_with_negative_keywords_decrease_score(self):
        """Negative keywords found only in pdf_texts must reduce the total score."""
        handler, _ = self._make_handler()

        command_without_pdf = ScoreTenderCommand(
            tender=_make_tender(titol="Obres de pavimentació"),
            filter_config=_make_filter_config(),
            pdf_texts=[],
        )
        result_without = await handler.handle(command_without_pdf)

        command_with_pdf = ScoreTenderCommand(
            tender=_make_tender(titol="Obres de pavimentació"),
            filter_config=_make_filter_config(),
            pdf_texts=["software saas plataforma digital aplicació web"],
        )
        result_with = await handler.handle(command_with_pdf)

        assert result_with.score.total < result_without.score.total

    # ------------------------------------------------------------------
    # RF-06 — Escala 0-100 (RN-03)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_maximum_achievable_score_is_100(self):
        """The best possible score must not exceed 100 pts (RF-06 / RN-03).

        Conditions to maximise: pressupost >= 1_000_000, many sector_positiu
        keywords, procediment obert and subcontractació in text.
        """
        handler, _ = self._make_handler()
        rich_pdf = (
            "obres construcció infraestructura reforma rehabilitació urbanisme "
            "enginyeria instal·lació maquinari manteniment obra civil edificació "
            "pavimentació canalització xarxa electricitat fontaneria climatització "
            "ascensor estructura fonamentació maquinaria escènica "
            "procediment obert subcontractació"
        )
        command = ScoreTenderCommand(
            tender=_make_tender(
                titol="obres de construcció infraestructura reforma rehabilitació",
                pressupost=2_000_000.0,
            ),
            filter_config=_make_filter_config(),
            pdf_texts=[rich_pdf],
        )
        result = await handler.handle(command)
        assert result.score.total <= 100, (
            f"Score {result.score.total} exceeds maximum of 100 pts"
        )

    @pytest.mark.asyncio
    async def test_best_score_reaches_100(self):
        """With optimal inputs, the score must reach exactly 100 pts (RF-06)."""
        handler, _ = self._make_handler()
        rich_pdf = (
            "obres construcció infraestructura reforma rehabilitació urbanisme "
            "enginyeria instal·lació maquinari manteniment obra civil edificació "
            "pavimentació canalització xarxa electricitat fontaneria climatització "
            "ascensor estructura fonamentació maquinaria escènica "
            "procediment obert subcontractació"
        )
        command = ScoreTenderCommand(
            tender=_make_tender(
                titol="obres de construcció",
                pressupost=2_000_000.0,
            ),
            filter_config=_make_filter_config(),
            pdf_texts=[rich_pdf],
        )
        result = await handler.handle(command)
        assert result.score.total == 100, (
            f"Expected 100 pts with optimal inputs, got {result.score.total}"
        )
