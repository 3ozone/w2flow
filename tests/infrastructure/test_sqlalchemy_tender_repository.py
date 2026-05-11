"""Tests d'integració per a SqlAlchemyTenderRepository.

Utilitza SQLite en memòria per no dependre de PostgreSQL.
ARRAY no és suportat per SQLite, per tant les classifications es guarden
com a TEXT (JSON serialitzat) en la taula creada manualment.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.domain.entities.tender import Tender
from app.infrastructure.repositories.sqlalchemy_tender_repository import SqlAlchemyTenderRepository

_CREATE_TENDERS_SQLITE = text("""
    CREATE TABLE tenders (
        expedient_id    TEXT    PRIMARY KEY NOT NULL,
        publicacio_id   INTEGER NOT NULL,
        organ           TEXT    NOT NULL,
        titol           TEXT    NOT NULL,
        codi_expedient  TEXT,
        pressupost      REAL,
        cpv_principal   TEXT,
        data_limit      DATETIME,
        durada_dies     INTEGER,
        tipus_contracte_id INTEGER,
        procediment_id  INTEGER,
        nuts_code       TEXT,
        classifications TEXT    NOT NULL DEFAULT '[]'
    )
""")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def session():
    """Sessió SQLite en memòria amb la taula tenders creada des de zero."""
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(_CREATE_TENDERS_SQLITE)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()
    yield db
    db.close()


def _make_tender(**kwargs) -> Tender:
    """Helper: crea un Tender mínim sobreescrivint només els camps indicats."""
    defaults = {
        "expedient_id": "f0b5b0e9-474a-482f-b917-908b85d2ca97",
        "publicacio_id": 300688406,
        "organ": "Ajuntament de Montagut i Oix",
        "titol": "Servei de socorrisme piscina 2026",
        "codi_expedient": None,
        "pressupost": None,
        "cpv_principal": None,
        "data_limit": None,
        "durada_dies": None,
        "tipus_contracte_id": None,
        "procediment_id": None,
        "nuts_code": None,
        "classifications": (),
    }
    defaults.update(kwargs)
    return Tender(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestIsDuplicate:
    """Tests per al mètode is_duplicate."""

    def test_retorna_false_si_no_existeix(self, session):
        """Retorna False quan l'expedient_id no és a la BD."""
        repo = SqlAlchemyTenderRepository(session)

        assert repo.is_duplicate("id-que-no-existeix") is False

    def test_retorna_true_si_ja_existeix(self, session):
        """Retorna True quan l'expedient_id ja és a la BD."""
        repo = SqlAlchemyTenderRepository(session)
        tender = _make_tender()

        repo.save(tender)
        session.flush()

        assert repo.is_duplicate(tender.expedient_id) is True


class TestSave:
    """Tests per al mètode save."""

    def test_guarda_tender_minimal(self, session):
        """Guarda un Tender amb els camps mínims obligatoris."""
        repo = SqlAlchemyTenderRepository(session)
        tender = _make_tender()

        repo.save(tender)
        session.flush()

        assert repo.is_duplicate(tender.expedient_id) is True

    def test_guarda_tender_complet(self, session):
        """Guarda un Tender amb tots els camps opcionals emplenats."""
        repo = SqlAlchemyTenderRepository(session)
        tender = _make_tender(
            codi_expedient="EXP-2026-001",
            pressupost=50000.0,
            cpv_principal="45000000-7",
            data_limit=datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc),
            durada_dies=180,
            tipus_contracte_id=1,
            procediment_id=2,
            nuts_code="ES512",
            classifications=("C", "G"),
        )

        repo.save(tender)
        session.flush()

        assert repo.is_duplicate(tender.expedient_id) is True

    def test_save_dos_tenders_diferents(self, session):
        """Guarda dos Tenders amb expedient_id diferent sense conflicte."""
        repo = SqlAlchemyTenderRepository(session)
        tender_a = _make_tender(expedient_id="aaaa-1111", publicacio_id=1)
        tender_b = _make_tender(expedient_id="bbbb-2222", publicacio_id=2)

        repo.save(tender_a)
        repo.save(tender_b)
        session.flush()

        assert repo.is_duplicate("aaaa-1111") is True
        assert repo.is_duplicate("bbbb-2222") is True
