"""Implementació SQLAlchemy del port TenderRepositoryPort (RN-06)."""
import json

from sqlalchemy.orm import Session

from app.application.ports.tender_repository_port import TenderRepositoryPort
from app.domain.entities.tender import Tender
from app.infrastructure.models.tender_model import TenderModel


class SqlAlchemyTenderRepository(TenderRepositoryPort):
    """Repositori de licitacions basat en SQLAlchemy.

    Implementa TenderRepositoryPort per a PostgreSQL (producció)
    i SQLite en memòria (tests d'integració).

    Les classifications es serialitzen com a JSON per compatibilitat
    amb SQLite en els tests (PostgreSQL usa ARRAY natiu).
    """

    def __init__(self, session: Session) -> None:
        """Inicialitza el repositori amb la sessió de BD injectada.

        Args:
            session: Sessió SQLAlchemy activa (gestionada externament).
        """
        self._session = session

    def is_duplicate(self, expedient_id: str) -> bool:
        """Comprova si una licitació ja existeix a la BD (RN-06).

        Args:
            expedient_id: Identificador únic de l'expedient.

        Returns:
            True si ja existeix a la base de dades, False en cas contrari.
        """
        return self._session.get(TenderModel, expedient_id) is not None

    def save(self, tender: Tender) -> None:
        """Persisteix una licitació a la base de dades.

        Converteix l'entitat de domini Tender al model ORM TenderModel
        i l'afegeix a la sessió. Les classifications (tuple) es
        serialitzen a JSON per compatibilitat amb SQLite.

        Args:
            tender: Entitat Tender a guardar.
        """
        classifications = (
            json.dumps(list(tender.classifications))
            if isinstance(tender.classifications, tuple)
            else tender.classifications
        )
        model = TenderModel(
            expedient_id=tender.expedient_id,
            publicacio_id=tender.publicacio_id,
            organ=tender.organ,
            titol=tender.titol,
            codi_expedient=tender.codi_expedient,
            pressupost=tender.pressupost,
            cpv_principal=tender.cpv_principal,
            data_limit=tender.data_limit,
            durada_dies=tender.durada_dies,
            tipus_contracte_id=tender.tipus_contracte_id,
            procediment_id=tender.procediment_id,
            nuts_code=tender.nuts_code,
            classifications=classifications,
        )
        self._session.add(model)

    def list_all(self) -> list[Tender]:
        """Retorna totes les licitacions de la BD ordenades per data_limit descendent.

        Les classifications es deserialitzen de JSON (SQLite) o ARRAY (PostgreSQL)
        a tuple[str, ...] per reconstruir l'entitat de domini.

        Returns:
            Llista de Tender de més recent a més antiga (per data_limit).
        """
        models = (
            self._session.query(TenderModel)
            .order_by(TenderModel.data_limit.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def count(self) -> int:
        """Retorna el nombre total de licitacions persistides a la base de dades.

        Returns:
            Nombre enter de registres existents.
        """
        return self._session.query(TenderModel).count()

    @staticmethod
    def _to_domain(model: TenderModel) -> Tender:
        """Converteix un TenderModel ORM a l'entitat de domini Tender.

        Args:
            model: Instància ORM obtinguda de la base de dades.

        Returns:
            Entitat Tender reconstruïda.
        """
        raw = model.classifications
        if isinstance(raw, str):
            classifications: tuple[str, ...] = tuple(json.loads(raw))
        elif isinstance(raw, list):
            classifications = tuple(raw)
        else:
            classifications = ()

        return Tender(
            expedient_id=model.expedient_id,
            publicacio_id=model.publicacio_id,
            organ=model.organ,
            titol=model.titol,
            codi_expedient=model.codi_expedient,
            pressupost=model.pressupost,
            cpv_principal=model.cpv_principal,
            data_limit=model.data_limit,
            durada_dies=model.durada_dies,
            tipus_contracte_id=model.tipus_contracte_id,
            procediment_id=model.procediment_id,
            nuts_code=model.nuts_code,
            classifications=classifications,
        )
