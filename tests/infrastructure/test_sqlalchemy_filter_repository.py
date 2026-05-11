"""Tests d'integració per a SqlAlchemyFilterRepository.

Utilitza SQLite en memòria per no dependre de PostgreSQL.
Les columnes ARRAY es guarden com a TEXT (JSON serialitzat) en la taula
creada manualment per a compatibilitat amb SQLite.
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.application.exceptions.application_errors import NoActiveFilterConfigError
from app.domain.value_objects.filter_config import FilterConfig
from app.infrastructure.repositories.sqlalchemy_filter_repository import SqlAlchemyFilterRepository

_CREATE_FILTER_CONFIGS_SQLITE = text("""
    CREATE TABLE filter_configs (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        is_active               INTEGER NOT NULL DEFAULT 0,
        created_at              DATETIME NOT NULL,
        tipus_expedient         INTEGER NOT NULL,
        fase_vigent             INTEGER NOT NULL,
        ambit                   INTEGER,
        tipus_contracte         INTEGER,
        procediment_adjudicacio INTEGER,
        cpv_codes               TEXT    NOT NULL DEFAULT '[]',
        pressupost_maxim        REAL    NOT NULL DEFAULT 0.0,
        nuts_codes              TEXT    NOT NULL DEFAULT '[]',
        classifications         TEXT    NOT NULL DEFAULT '[]',
        durada_minima_dies      INTEGER NOT NULL DEFAULT 0,
        durada_maxima_dies      INTEGER NOT NULL DEFAULT 0,
        max_licitacions         INTEGER NOT NULL DEFAULT 20
    )
""")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def session():
    """Sessió SQLite en memòria amb la taula filter_configs creada des de zero."""
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(_CREATE_FILTER_CONFIGS_SQLITE)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()
    yield db
    db.close()


def _make_config(**kwargs) -> FilterConfig:
    """Helper: crea un FilterConfig mínim sobreescrivint els camps indicats."""
    defaults = {
        "tipus_expedient": 1,
        "fase_vigent": 0,
    }
    defaults.update(kwargs)
    return FilterConfig(**defaults)


# ---------------------------------------------------------------------------
# Tests — save
# ---------------------------------------------------------------------------

class TestSave:
    """Tests per al mètode save."""

    def test_guarda_config_minimal(self, session):
        """Guarda una FilterConfig amb els camps mínims obligatoris."""
        repo = SqlAlchemyFilterRepository(session)
        config = _make_config()

        repo.save(config)
        session.flush()

        result = repo.list_all()
        assert len(result) == 1

    def test_save_marca_anterior_com_inactiva(self, session):
        """Quan es guarda una nova config activa, les anteriors es desactiven."""
        repo = SqlAlchemyFilterRepository(session)
        config_a = _make_config(tipus_expedient=1)
        config_b = _make_config(tipus_expedient=2)

        repo.save(config_a)
        session.flush()
        repo.save(config_b)
        session.flush()

        active = repo.get_active()
        assert active.tipus_expedient == 2

    def test_save_config_completa(self, session):
        """Guarda una FilterConfig amb tots els camps opcionals."""
        repo = SqlAlchemyFilterRepository(session)
        config = _make_config(
            ambit=3,
            tipus_contracte=2,
            procediment_adjudicacio=1,
            cpv_codes=("45000000-7", "71000000-8"),
            pressupost_maxim=100000.0,
            nuts_codes=("ES512",),
            classifications=("C", "G"),
            durada_minima_dies=30,
            durada_maxima_dies=365,
        )

        repo.save(config)
        session.flush()

        active = repo.get_active()
        assert active.cpv_codes == ("45000000-7", "71000000-8")
        assert active.nuts_codes == ("ES512",)
        assert active.classifications == ("C", "G")
        assert active.pressupost_maxim == 100000.0

    def test_save_i_recupera_max_licitacions(self, session):
        """Guarda i recupera max_licitacions correctament (RN-13)."""
        repo = SqlAlchemyFilterRepository(session)
        config = _make_config(max_licitacions=50)

        repo.save(config)
        session.flush()

        active = repo.get_active()
        assert active.max_licitacions == 50


# ---------------------------------------------------------------------------
# Tests — get_active
# ---------------------------------------------------------------------------

class TestGetActive:
    """Tests per al mètode get_active."""

    def test_llança_excepció_si_no_hi_ha_activa(self, session):
        """Llança NoActiveFilterConfigError quan la taula és buida."""
        repo = SqlAlchemyFilterRepository(session)

        with pytest.raises(NoActiveFilterConfigError):
            repo.get_active()

    def test_retorna_la_config_activa(self, session):
        """Retorna la FilterConfig marcada com a activa."""
        repo = SqlAlchemyFilterRepository(session)
        config = _make_config(tipus_expedient=5, fase_vigent=2)

        repo.save(config)
        session.flush()

        active = repo.get_active()
        assert active.tipus_expedient == 5
        assert active.fase_vigent == 2


# ---------------------------------------------------------------------------
# Tests — list_all
# ---------------------------------------------------------------------------

class TestListAll:
    """Tests per al mètode list_all."""

    def test_retorna_llista_buida_si_no_hi_ha_configs(self, session):
        """Retorna llista buida quan no hi ha cap configuració guardada."""
        repo = SqlAlchemyFilterRepository(session)

        assert repo.list_all() == []

    def test_retorna_totes_les_configs(self, session):
        """Retorna totes les configuracions guardades."""
        repo = SqlAlchemyFilterRepository(session)

        repo.save(_make_config(tipus_expedient=1))
        session.flush()
        repo.save(_make_config(tipus_expedient=2))
        session.flush()

        result = repo.list_all()
        assert len(result) == 2
