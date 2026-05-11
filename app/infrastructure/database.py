"""Configuració de SQLAlchemy: engine, sessió i Base declarativa."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import Settings

_settings = Settings()

engine = create_engine(
    _settings.database_url,
    pool_pre_ping=True,  # verifica la connexió abans de cada ús
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Classe base de la qual hereten tots els models ORM del projecte."""
