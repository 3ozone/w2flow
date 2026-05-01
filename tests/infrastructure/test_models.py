"""Tests for SQLAlchemy ORM models — mapping verification using SQLite in-memory."""

from datetime import date
from sqlalchemy import create_engine, inspect
import pytest
from sqlalchemy.orm import Session

from app.infrastructure.repositories.models import Base, TenderModel, ScoreModel, DocumentModel


@pytest.fixture(scope="module")
def engine():
    """SQLite in-memory engine with all tables created."""
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def session(engine):
    """Transactional session rolled back after each test."""
    with Session(engine) as sess:
        with sess.begin():
            yield sess
            sess.rollback()


class TestTenderModel:
    """Verify TenderModel table structure."""

    def test_table_name(self):
        """Table name must be 'tenders'."""
        assert TenderModel.__tablename__ == "tenders"

    def test_required_columns_exist(self, engine):
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("tenders")}
        expected = {
            "expedient_id", "publicacio_id", "titol", "organ",
            "pressupost", "codi_expedient", "fase", "data_publicacio",
        }
        assert expected.issubset(columns)

    def test_primary_key_is_expedient_id(self, engine):
        inspector = inspect(engine)
        pk = inspector.get_pk_constraint("tenders")
        assert "expedient_id" in pk["constrained_columns"]

    def test_insert_and_retrieve(self, session):
        row = TenderModel(
            expedient_id="uuid-1",
            publicacio_id=42,
            titol="Obres de pavimentació",
            organ="Ajuntament de Girona",
            pressupost=300_000.0,
            codi_expedient="EXP-001",
            fase="0",
            data_publicacio=date.today(),
        )
        session.add(row)
        session.flush()
        fetched = session.get(TenderModel, "uuid-1")
        assert fetched.titol == "Obres de pavimentació"
        assert fetched.pressupost == 300_000.0


class TestScoreModel:
    """Verify ScoreModel table structure."""

    def test_table_name(self):
        assert ScoreModel.__tablename__ == "scores"

    def test_required_columns_exist(self, engine):
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("scores")}
        expected = {
            "id", "expedient_id", "total", "detall",
            "paraules_clau_trobades", "penalitzacions", "recomanacio",
        }
        assert expected.issubset(columns)

    def test_foreign_key_to_tenders(self, engine):
        inspector = inspect(engine)
        fks = inspector.get_foreign_keys("scores")
        fk_columns = {fk["constrained_columns"][0] for fk in fks}
        assert "expedient_id" in fk_columns

    def test_insert_with_tender(self, session):
        tender = TenderModel(
            expedient_id="uuid-score",
            publicacio_id=1,
            titol="Test tender",
            organ="Org",
            pressupost=100_000.0,
            codi_expedient="EXP-S",
            fase="0",
            data_publicacio=date.today(),
        )
        session.add(tender)
        session.flush()

        score = ScoreModel(
            expedient_id="uuid-score",
            total=55,
            detall='{"pressupost": 25}',
            paraules_clau_trobades='["obres"]',
            penalitzacions='[]',
            recomanacio="RECOMANADA",
        )
        session.add(score)
        session.flush()
        assert score.total == 55


class TestDocumentModel:
    """Verify DocumentModel table structure."""

    def test_table_name(self):
        assert DocumentModel.__tablename__ == "documents"

    def test_required_columns_exist(self, engine):
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("documents")}
        expected = {
            "expedient_id", "doc_id", "titol", "hash",
            "mida_kb", "file_path", "type",
        }
        assert expected.issubset(columns)

    def test_composite_primary_key(self, engine):
        inspector = inspect(engine)
        pk = inspector.get_pk_constraint("documents")
        assert set(pk["constrained_columns"]) == {"expedient_id", "doc_id"}

    def test_insert_and_retrieve(self, session):
        tender = TenderModel(
            expedient_id="uuid-doc",
            publicacio_id=1,
            titol="Test tender",
            organ="Org",
            pressupost=50_000.0,
            codi_expedient="EXP-D",
            fase="0",
            data_publicacio=date.today(),
        )
        session.add(tender)
        session.flush()

        doc = DocumentModel(
            expedient_id="uuid-doc",
            doc_id=99,
            titol="Plec de clàusules",
            hash="abc123",
            mida_kb=512.0,
            file_path="/files/uuid-doc/99.pdf",
            type="PCAP",
        )
        session.add(doc)
        session.flush()
        fetched = session.get(DocumentModel, ("uuid-doc", 99))
        assert fetched.titol == "Plec de clàusules"
