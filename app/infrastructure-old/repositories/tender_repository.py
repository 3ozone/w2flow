"""SQLAlchemy implementation of TenderRepositoryPort."""

from __future__ import annotations

import json

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.ports.tender_repository_port import TenderRepositoryPort
from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.exceptions.duplicate_tender_error import DuplicateTenderError
from app.domain.value_objects.score import Score
from app.infrastructure.repositories.models import ScoreModel, TenderModel

try:
    from psycopg2.errors import UniqueViolation as _UniqueViolation
except ImportError:  # fallback if psycopg2 not available (e.g. in unit tests)
    _UniqueViolation = None


class TenderRepository(TenderRepositoryPort):
    """Persists and retrieves Tenders and ScoredTenders using SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def save(self, tender: Tender) -> None:
        """Persist a tender. Raises DuplicateTenderError if already exists."""
        model = TenderModel(
            expedient_id=tender.expedient_id,
            publicacio_id=tender.publicacio_id,
            titol=tender.titol,
            organ=tender.organ,
            pressupost=tender.pressupost,
            codi_expedient=tender.codi_expedient,
            fase=tender.fase,
            data_publicacio=tender.data_publicacio,
            codi_cpv=tender.codi_cpv,
            termini_execucio=tender.termini_execucio,
            data_limit_presentacio=tender.data_limit_presentacio,
        )
        self._session.add(model)
        try:
            self._session.flush()
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            # Only treat genuine duplicate-key violations as DuplicateTenderError.
            # Other IntegrityErrors (e.g. NOT NULL, FK violations) must propagate so
            # the caller knows the tender was NOT persisted.
            if _UniqueViolation is not None and isinstance(exc.orig, _UniqueViolation):
                raise DuplicateTenderError(
                    f"Tender with expedient_id '{tender.expedient_id}' already exists."
                )
            raise

    async def get_by_id(self, expedient_id: str) -> Tender | None:
        """Return the tender with the given expedient_id, or None."""
        model = self._session.get(TenderModel, expedient_id)
        if model is None:
            return None
        return self._to_tender(model)

    async def save_scored(self, scored_tender: ScoredTender) -> None:
        """Persist a scored tender (score row linked to the tender)."""
        score = scored_tender.score
        model = ScoreModel(
            expedient_id=score.expedient_id,
            total=score.total,
            detall=json.dumps(score.detall),
            paraules_clau_trobades=json.dumps(
                list(score.paraules_clau_trobades)),
            penalitzacions=json.dumps(list(score.penalitzacions)),
            recomanacio=score.recomanacio,
        )
        self._session.add(model)
        self._session.flush()
        self._session.commit()

    async def list_scored(self, page: int = 0, size: int = 20) -> list[ScoredTender]:
        """Return a paginated list of scored tenders."""
        score_models = (
            self._session.query(ScoreModel)
            .offset(page * size)
            .limit(size)
            .all()
        )
        result = []
        for sm in score_models:
            tender_model = self._session.get(TenderModel, sm.expedient_id)
            if tender_model is None:
                continue
            tender = self._to_tender(tender_model)
            score = Score(
                expedient_id=sm.expedient_id,
                total=sm.total,
                detall=json.loads(sm.detall),
                paraules_clau_trobades=tuple(
                    json.loads(sm.paraules_clau_trobades)),
                penalitzacions=tuple(json.loads(sm.penalitzacions)),
                recomanacio=sm.recomanacio,
            )
            result.append(ScoredTender(
                tender=tender, score=score, requirements=None))
        return result

    async def list_documents(self, expedient_id: str) -> list:
        """Return all documents stored for the given expedient_id."""
        from app.domain.entities.document import Document
        from app.domain.value_objects.document_type import DocumentType
        from app.infrastructure.repositories.models import DocumentModel
        models = (
            self._session.query(DocumentModel)
            .filter(DocumentModel.expedient_id == expedient_id)
            .all()
        )
        return [
            Document(
                expedient_id=m.expedient_id,
                doc_id=m.doc_id,
                titol=m.titol,
                hash=m.hash,
                mida_kb=m.mida_kb,
                file_path=m.file_path,
                type=DocumentType(m.type),
            )
            for m in models
        ]

    async def delete(self, expedient_id: str) -> None:
        """Delete a tender and all its associated scores and documents."""
        from app.infrastructure.repositories.models import DocumentModel
        self._session.query(ScoreModel).filter(
            ScoreModel.expedient_id == expedient_id
        ).delete(synchronize_session=False)
        self._session.query(DocumentModel).filter(
            DocumentModel.expedient_id == expedient_id
        ).delete(synchronize_session=False)
        self._session.query(TenderModel).filter(
            TenderModel.expedient_id == expedient_id
        ).delete(synchronize_session=False)
        self._session.flush()
        self._session.commit()

    @staticmethod
    def _to_tender(model: TenderModel) -> Tender:
        return Tender(
            expedient_id=model.expedient_id,
            publicacio_id=model.publicacio_id,
            titol=model.titol,
            organ=model.organ,
            pressupost=model.pressupost,
            codi_expedient=model.codi_expedient,
            fase=model.fase,
            data_publicacio=model.data_publicacio,
            codi_cpv=model.codi_cpv,
            termini_execucio=model.termini_execucio,
            data_limit_presentacio=model.data_limit_presentacio,
        )
