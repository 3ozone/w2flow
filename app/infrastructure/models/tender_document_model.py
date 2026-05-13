"""Model ORM per a la taula tender_documents (Fase J, RF-09, RF-10)."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class TenderDocumentModel(Base):
    """Representació ORM d'un document adjunt d'una licitació.

    Cada fila correspon a un PDF descarregat durant el pipeline.
    El camp comentari_llm s'omple en una fase posterior del pipeline
    quan el LLM analitza el document.
    """

    __tablename__ = "tender_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expedient_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenders.expedient_id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    filepath: Mapped[str] = mapped_column(Text, nullable=False)
    comentari_llm: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
