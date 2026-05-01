"""Integration tests for DocumentRepository against a real PostgreSQL database."""

from datetime import date
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.domain.entities.document import Document
from app.domain.value_objects.document_type import DocumentType
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.models import Base, TenderModel


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
def session_with_tender(session):
    """Session with a pre-inserted tender row to satisfy FK constraint."""
    tender = TenderModel(
        expedient_id="uuid-doc-1",
        publicacio_id=1,
        titol="Obres de construcció",
        organ="Ajuntament de Girona",
        pressupost=300_000.0,
        codi_expedient="EXP-doc-1",
        fase="0",
        data_publicacio=date.today(),
    )
    session.add(tender)
    session.flush()
    return session


@pytest.fixture
def repository(session_with_tender):
    """DocumentRepository backed by the transactional test session."""
    return DocumentRepository(session=session_with_tender)


def _make_document(doc_id: int = 1, expedient_id: str = "uuid-doc-1") -> Document:
    return Document(
        expedient_id=expedient_id,
        doc_id=doc_id,
        titol="Plec de clàusules administratives",
        hash="abc123hash",
        mida_kb=512.0,
        file_path=f"/files/{expedient_id}/{doc_id}.pdf",
        type=DocumentType.PCAP,
    )


class TestDocumentRepositorySave:
    """Tests for DocumentRepository.save()."""

    @pytest.mark.asyncio
    async def test_save_returns_file_path(self, repository):
        """save() must return a non-empty file path string."""
        doc = _make_document()
        path = await repository.save(doc, content=b"PDF content")
        assert isinstance(path, str)
        assert len(path) > 0

    @pytest.mark.asyncio
    async def test_save_persists_document(self, repository, session_with_tender):
        """save() must insert the document into the database."""
        doc = _make_document(doc_id=2)
        await repository.save(doc, content=b"PDF content")
        session_with_tender.flush()
        from sqlalchemy import text
        result = session_with_tender.execute(
            text(
                "SELECT doc_id FROM documents WHERE expedient_id = :eid AND doc_id = :did"),
            {"eid": doc.expedient_id, "did": doc.doc_id},
        ).fetchone()
        assert result is not None

    @pytest.mark.asyncio
    async def test_save_duplicate_is_idempotent(self, repository):
        """save() called twice with same (expedient_id, doc_id) must not raise."""
        doc = _make_document(doc_id=3)
        await repository.save(doc, content=b"first")
        path = await repository.save(doc, content=b"second")
        assert path is not None


class TestDocumentRepositoryExists:
    """Tests for DocumentRepository.exists()."""

    @pytest.mark.asyncio
    async def test_exists_returns_false_before_save(self, repository):
        """exists() must return False for a document not yet stored."""
        result = await repository.exists("uuid-doc-1", 999)
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_returns_true_after_save(self, repository):
        """exists() must return True after the document has been saved."""
        doc = _make_document(doc_id=4)
        await repository.save(doc, content=b"PDF")
        result = await repository.exists(doc.expedient_id, doc.doc_id)
        assert result is True


class TestDocumentRepositoryGetPath:
    """Tests for DocumentRepository.get_path()."""

    @pytest.mark.asyncio
    async def test_get_path_returns_none_for_unknown(self, repository):
        """get_path() must return None for a document not stored."""
        result = await repository.get_path("uuid-doc-1", 888)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_path_returns_path_after_save(self, repository):
        """get_path() must return the stored file path after save()."""
        doc = _make_document(doc_id=5)
        await repository.save(doc, content=b"PDF")
        path = await repository.get_path(doc.expedient_id, doc.doc_id)
        assert path == doc.file_path
