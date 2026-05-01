"""Integration tests for TenderRepository against a real PostgreSQL database."""

from datetime import date
import pytest

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import settings
from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.value_objects.score import Score
from app.infrastructure.repositories.models import Base
from app.infrastructure.repositories.tender_repository import TenderRepository


@pytest.fixture(scope="module")
def engine():
    """Create engine and ensure all tables exist."""
    eng = create_engine(settings.database_url)
    Base.metadata.create_all(eng)
    yield eng


@pytest.fixture
def session(engine):
    """Transactional session rolled back after each test — no dirty data."""
    with Session(engine) as sess:
        sess.begin()
        yield sess
        sess.rollback()


@pytest.fixture
def repository(session):
    """TenderRepository backed by the transactional test session."""
    return TenderRepository(session=session)


def _make_tender(expedient_id: str = "uuid-repo-1") -> Tender:
    return Tender(
        expedient_id=expedient_id,
        publicacio_id=10,
        titol="Obres de construcció de la nova biblioteca",
        organ="Ajuntament de Girona",
        pressupost=300_000.0,
        codi_expedient=f"EXP-{expedient_id}",
        fase="0",
        data_publicacio=date.today(),
    )


def _make_scored_tender(expedient_id: str = "uuid-repo-1") -> ScoredTender:
    tender = _make_tender(expedient_id)
    score = Score(
        expedient_id=expedient_id,
        total=60,
        detall={"pressupost": 25, "sector_positiu": 10, "sector_negatiu": 0},
        paraules_clau_trobades=("obres",),
        penalitzacions=(),
        recomanacio="RECOMANADA",
    )
    return ScoredTender(tender=tender, score=score, requirements=None)


class TestTenderRepositorySave:
    """Tests for TenderRepository.save()."""

    @pytest.mark.asyncio
    async def test_save_persists_tender(self, repository, session):
        """save() must insert the tender into the database."""
        tender = _make_tender()
        await repository.save(tender)
        session.flush()
        result = session.execute(
            text("SELECT expedient_id FROM tenders WHERE expedient_id = :id"),
            {"id": tender.expedient_id},
        ).fetchone()
        assert result is not None

    @pytest.mark.asyncio
    async def test_save_stores_correct_fields(self, repository, session):
        """save() must persist all tender fields correctly."""
        tender = _make_tender()
        await repository.save(tender)
        session.flush()
        row = session.execute(
            text("SELECT titol, pressupost, organ FROM tenders WHERE expedient_id = :id"),
            {"id": tender.expedient_id},
        ).fetchone()
        assert row.titol == tender.titol
        assert row.pressupost == tender.pressupost
        assert row.organ == tender.organ

    @pytest.mark.asyncio
    async def test_save_duplicate_raises_duplicate_tender_error(self, repository):
        """save() must raise DuplicateTenderError when expedient_id already exists."""
        from app.domain.exceptions.duplicate_tender_error import DuplicateTenderError

        tender = _make_tender()
        await repository.save(tender)
        with pytest.raises(DuplicateTenderError):
            await repository.save(tender)


class TestTenderRepositoryGetById:
    """Tests for TenderRepository.get_by_id()."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_tender(self, repository):
        """get_by_id() must return a Tender for an existing expedient_id."""
        tender = _make_tender()
        await repository.save(tender)
        result = await repository.get_by_id(tender.expedient_id)
        assert isinstance(result, Tender)
        assert result.expedient_id == tender.expedient_id

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_unknown(self, repository):
        """get_by_id() must return None when expedient_id does not exist."""
        result = await repository.get_by_id("non-existent-id")
        assert result is None


class TestTenderRepositorySaveScored:
    """Tests for TenderRepository.save_scored()."""

    @pytest.mark.asyncio
    async def test_save_scored_persists_score(self, repository, session):
        """save_scored() must insert a score row linked to the tender."""
        scored = _make_scored_tender()
        await repository.save(scored.tender)
        await repository.save_scored(scored)
        session.flush()
        row = session.execute(
            text("SELECT total, recomanacio FROM scores WHERE expedient_id = :id"),
            {"id": scored.tender.expedient_id},
        ).fetchone()
        assert row is not None
        assert row.total == 60
        assert row.recomanacio == "RECOMANADA"


class TestTenderRepositoryListScored:
    """Tests for TenderRepository.list_scored()."""

    @pytest.mark.asyncio
    async def test_list_scored_returns_list(self, repository):
        """list_scored() must return a list."""
        result = await repository.list_scored()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_scored_returns_saved_items(self, repository):
        """list_scored() must include previously saved scored tenders."""
        scored = _make_scored_tender("uuid-list-1")
        await repository.save(scored.tender)
        await repository.save_scored(scored)
        result = await repository.list_scored()
        ids = [st.tender.expedient_id for st in result]
        assert "uuid-list-1" in ids

    @pytest.mark.asyncio
    async def test_list_scored_respects_pagination(self, repository):
        """list_scored(page=0, size=1) must return at most 1 item."""
        for i in range(3):
            scored = _make_scored_tender(f"uuid-page-{i}")
            await repository.save(scored.tender)
            await repository.save_scored(scored)
        result = await repository.list_scored(page=0, size=1)
        assert len(result) <= 1
