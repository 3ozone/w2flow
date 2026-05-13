"""Implementació SQLAlchemy del TenderDocumentRepositoryPort (RF-09)."""
from datetime import timezone

from sqlalchemy.orm import Session

from app.application.ports.tender_document_repository_port import TenderDocumentRepositoryPort
from app.domain.entities.tender_document import TenderDocument
from app.infrastructure.models.tender_document_model import TenderDocumentModel


class SqlAlchemyTenderDocumentRepository(TenderDocumentRepositoryPort):
    """Persisteix i consulta TenderDocument usant SQLAlchemy i PostgreSQL."""

    def __init__(self, session: Session) -> None:
        """Inicialitza el repositori amb la sessió de base de dades.

        Args:
            session: Sessió SQLAlchemy activa.
        """
        self._session = session

    def save(self, document: TenderDocument) -> None:
        """Persisteix un document adjunt a la base de dades.

        Args:
            document: Entitat TenderDocument a guardar.
        """
        model = TenderDocumentModel(
            expedient_id=document.expedient_id,
            filename=document.filename,
            filepath=document.filepath,
            comentari_llm=document.comentari_llm,
            created_at=document.created_at,
        )
        self._session.add(model)
        self._session.flush()

    def list_by_expedient(self, expedient_id: str) -> list[TenderDocument]:
        """Retorna tots els documents d'un expedient ordenats per nom de fitxer.

        Args:
            expedient_id: UUID de la licitació.

        Returns:
            Llista de TenderDocument, buida si no n'hi ha cap.
        """
        rows = (
            self._session.query(TenderDocumentModel)
            .filter(TenderDocumentModel.expedient_id == expedient_id)
            .order_by(TenderDocumentModel.filename)
            .all()
        )
        return [
            TenderDocument(
                expedient_id=row.expedient_id,
                filename=row.filename,
                filepath=row.filepath,
                comentari_llm=row.comentari_llm,
                created_at=row.created_at.replace(tzinfo=timezone.utc)
                if row.created_at.tzinfo is None
                else row.created_at,
            )
            for row in rows
        ]

    def update_comentari(self, expedient_id: str, filename: str, comentari: str) -> None:
        """Actualitza el comentari LLM d'un document adjunt.

        Args:
            expedient_id: UUID de la licitació.
            filename:     Nom del fitxer PDF.
            comentari:    Comentari narratiu generat pel LLM (RF-10).
        """
        row = (
            self._session.query(TenderDocumentModel)
            .filter(
                TenderDocumentModel.expedient_id == expedient_id,
                TenderDocumentModel.filename == filename,
            )
            .first()
        )
        if row is not None:
            row.comentari_llm = comentari
            self._session.flush()
