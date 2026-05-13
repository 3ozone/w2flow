"""Model ORM per a la taula tenders (RF-02, RF-03, RNF-06)."""
from datetime import datetime

from sqlalchemy import ARRAY, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class TenderModel(Base):
    """Representació ORM d'una licitació pública a la base de dades.

    Mapeja tots els camps de l'entitat de domini Tender a columnes PostgreSQL.
    Les classifications s'emmagatzemen com a ARRAY de text.
    """

    __tablename__ = "tenders"

    # --- Identificació ---
    expedient_id: Mapped[str] = mapped_column(String, primary_key=True)
    publicacio_id: Mapped[int] = mapped_column(Integer, nullable=False)
    organ: Mapped[str] = mapped_column(Text, nullable=False)
    titol: Mapped[str] = mapped_column(Text, nullable=False)

    # --- Detall ---
    codi_expedient: Mapped[str | None] = mapped_column(String, nullable=True)
    pressupost: Mapped[float | None] = mapped_column(Float, nullable=True)
    cpv_principal: Mapped[str | None] = mapped_column(
        String(20), nullable=True)
    data_limit: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    durada_dies: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # --- Filtres ---
    tipus_contracte_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True)
    procediment_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nuts_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    classifications: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list)

    # --- Puntuació i recomanació (Fase J, RNF-06) ---
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    score_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_traffic_light: Mapped[str | None] = mapped_column(
        String(10), nullable=True)
    score_detall: Mapped[str | None] = mapped_column(
        Text, nullable=True)  # JSON serialitzat
    recomendacio: Mapped[str | None] = mapped_column(Text, nullable=True)
