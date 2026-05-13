"""Implementació SQLAlchemy del port FilterRepositoryPort (RF-03)."""
import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.application.exceptions.application_errors import NoActiveFilterConfigError
from app.application.ports.filter_repository_port import FilterRepositoryPort
from app.domain.value_objects.filter_config import FilterConfig
from app.infrastructure.models.filter_config_model import FilterConfigModel


class SqlAlchemyFilterRepository(FilterRepositoryPort):
    """Repositori de configuracions de filtre basat en SQLAlchemy.

    Implementa FilterRepositoryPort per a PostgreSQL (producció)
    i SQLite en memòria (tests d'integració).

    Les tuples de strings es serialitzen com a JSON per compatibilitat
    amb SQLite. En PostgreSQL s'emmagatzemen com a ARRAY natiu.

    Invariant: sempre hi ha com a màxim una fila amb is_active=True.
    """

    def __init__(self, session: Session) -> None:
        """Inicialitza el repositori amb la sessió de BD injectada.

        Detecta si la BD subjacent és SQLite (tests) per adaptar la
        serialització dels camps ARRAY.

        Args:
            session: Sessió SQLAlchemy activa (gestionada externament).
        """
        self._session = session
        try:
            dialect = session.get_bind().dialect.name
            self._sqlite_mode = dialect == "sqlite"
        except Exception:
            self._sqlite_mode = False

    def save(self, config: FilterConfig) -> None:
        """Persisteix una nova configuració de filtre i la marca com a activa.

        Desactiva totes les configuracions anteriors per mantenir l'invariant
        que només hi ha una configuració activa a la vegada.

        Args:
            config: FilterConfig a guardar.
        """
        self._session.query(FilterConfigModel).filter(
            FilterConfigModel.is_active.is_(True)
        ).update({"is_active": False})

        model = FilterConfigModel(
            is_active=True,
            created_at=datetime.now(timezone.utc),
            tipus_expedient=config.tipus_expedient,
            fase_vigent=config.fase_vigent,
            ambit=config.ambit,
            tipus_contracte=config.tipus_contracte,
            procediment_adjudicacio=config.procediment_adjudicacio,
            cpv_codes=self._serialize(config.cpv_codes),
            pressupost_maxim=config.pressupost_maxim,
            nuts_codes=self._serialize(config.nuts_codes),
            classifications=self._serialize(config.classifications),
            durada_minima_dies=config.durada_minima_dies,
            durada_maxima_dies=config.durada_maxima_dies,
            max_licitacions=config.max_licitacions,
        )
        self._session.add(model)

    def get_active(self) -> FilterConfig:
        """Recupera la configuració de filtre activa.

        Returns:
            FilterConfig activa.

        Raises:
            NoActiveFilterConfigError: Si no hi ha cap configuració activa.
        """
        model = (
            self._session.query(FilterConfigModel)
            .filter(FilterConfigModel.is_active.is_(True))
            .first()
        )
        if model is None:
            raise NoActiveFilterConfigError()
        return self._to_domain(model)

    def list_all(self) -> list[FilterConfig]:
        """Recupera totes les configuracions de filtre guardades.

        Returns:
            Llista de FilterConfig ordenada per data de creació descendent.
        """
        models = (
            self._session.query(FilterConfigModel)
            .order_by(FilterConfigModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    # ---------------------------------------------------------------------------
    # Helpers privats
    # ---------------------------------------------------------------------------

    def _serialize(self, value: tuple[str, ...]) -> object:
        """Serialitza una tupla de strings per a la BD.

        Per a SQLite (tests) retorna un string JSON perquè la columna és TEXT.
        Per a PostgreSQL retorna una llista per a la columna ARRAY nativa.

        Args:
            value: Tupla de strings a serialitzar.

        Returns:
            JSON string per a SQLite, llista Python per a PostgreSQL.
        """
        if self._sqlite_mode:
            return json.dumps(list(value))
        return list(value)

    @staticmethod
    def _deserialize(value: object) -> tuple[str, ...]:
        """Deserialitza un valor JSON o ARRAY a tuple de strings."""
        if isinstance(value, str):
            return tuple(json.loads(value))
        if isinstance(value, list):
            return tuple(value)
        return ()

    def _to_domain(self, model: FilterConfigModel) -> FilterConfig:
        """Converteix un FilterConfigModel ORM en un FilterConfig de domini.

        Args:
            model: Registre ORM llegit de la BD.

        Returns:
            FilterConfig immutable amb els valors del model.
        """
        return FilterConfig(
            tipus_expedient=model.tipus_expedient,
            fase_vigent=model.fase_vigent,
            ambit=model.ambit,
            tipus_contracte=model.tipus_contracte,
            procediment_adjudicacio=model.procediment_adjudicacio,
            cpv_codes=self._deserialize(model.cpv_codes),
            pressupost_maxim=model.pressupost_maxim,
            nuts_codes=self._deserialize(model.nuts_codes),
            classifications=self._deserialize(model.classifications),
            durada_minima_dies=model.durada_minima_dies,
            durada_maxima_dies=model.durada_maxima_dies,
            max_licitacions=model.max_licitacions,
        )
