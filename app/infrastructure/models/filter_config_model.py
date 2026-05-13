"""Model ORM per a la taula filter_configs (RF-03)."""
from datetime import datetime, timezone

from sqlalchemy import ARRAY, Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class FilterConfigModel(Base):
    """Representació ORM d'una configuració de filtre guardada per l'usuari.

    Mapeja tots els camps de FilterConfig a columnes PostgreSQL.
    El camp is_active indica quina configuració és la vigent.
    Les tuples de strings s'emmagatzemen com a ARRAY de text.
    """

    __tablename__ = "filter_configs"

    # --- Metadades ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # --- Filtres natius obligatoris ---
    tipus_expedient: Mapped[int] = mapped_column(Integer, nullable=False)
    fase_vigent: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Filtres natius opcionals ---
    ambit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tipus_contracte: Mapped[int | None] = mapped_column(Integer, nullable=True)
    procediment_adjudicacio: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # --- Filtres post-fetch ---
    cpv_codes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    pressupost_maxim: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    nuts_codes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    classifications: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    durada_minima_dies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    durada_maxima_dies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Configuració del pipeline (RN-13) ---
    max_licitacions: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
