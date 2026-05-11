"""SQLAlchemy ORM models for w2flow."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class TenderModel(Base):
    """ORM mapping for the tenders table."""

    __tablename__ = "tenders"

    expedient_id: Mapped[str] = mapped_column(String, primary_key=True)
    publicacio_id: Mapped[int] = mapped_column(Integer, nullable=False)
    titol: Mapped[str] = mapped_column(String, nullable=False)
    organ: Mapped[str] = mapped_column(String, nullable=False)
    pressupost: Mapped[float | None] = mapped_column(Float, nullable=True)
    codi_expedient: Mapped[str] = mapped_column(String, nullable=False)
    fase: Mapped[str] = mapped_column(String, nullable=False)
    data_publicacio: Mapped[date] = mapped_column(Date, nullable=False)
    codi_cpv: Mapped[str | None] = mapped_column(String, nullable=True)
    termini_execucio: Mapped[str | None] = mapped_column(String, nullable=True)
    data_limit_presentacio: Mapped[str | None] = mapped_column(String, nullable=True)


class ScoreModel(Base):
    """ORM mapping for the scores table."""

    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expedient_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenders.expedient_id"), nullable=False
    )
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    detall: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    paraules_clau_trobades: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    penalitzacions: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    recomanacio: Mapped[str] = mapped_column(String, nullable=False)


class DocumentModel(Base):
    """ORM mapping for the documents table."""

    __tablename__ = "documents"

    expedient_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenders.expedient_id"), primary_key=True
    )
    doc_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titol: Mapped[str] = mapped_column(String, nullable=False)
    hash: Mapped[str] = mapped_column(String, nullable=False)
    mida_kb: Mapped[float] = mapped_column(Float, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
