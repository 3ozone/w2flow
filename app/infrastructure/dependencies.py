"""Composition Root — proveïdors de dependències per a FastAPI (dependency injection).

Aquest és l'únic lloc del projecte on s'instancien implementacions concretes
d'infraestructura. Els routers i use cases només coneixen les abstraccions (ports).

Flux de dependències:
  Settings → engine → SessionLocal → repositoris → use cases → routers
"""
from collections.abc import Generator
from pathlib import Path

from sqlalchemy.orm import Session

from app.application.use_cases.fetch_candidates_use_case import FetchCandidatesUseCase
from app.application.use_cases.run_pipeline_use_case import RunPipelineUseCase
from app.config import Settings
from app.infrastructure.database import SessionLocal
from app.infrastructure.repositories.sqlalchemy_filter_repository import SqlAlchemyFilterRepository
from app.infrastructure.repositories.sqlalchemy_tender_document_repository import SqlAlchemyTenderDocumentRepository
from app.infrastructure.repositories.sqlalchemy_tender_repository import SqlAlchemyTenderRepository
from app.infrastructure.services.contractacio_publica_client import ContractacioPublicaClient
from app.infrastructure.services.local_file_document_storage import LocalFileDocumentStorage
from app.infrastructure.services.timbal_nlp_analyser import TimbalNlpAnalyser

_settings = Settings()


# ---------------------------------------------------------------------------
# Proveïdor de sessió SQLAlchemy (una sessió per request HTTP)
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """Proveeix una sessió SQLAlchemy per al cicle de vida d'un request FastAPI.

    Fa un rollback automàtic si es produeix una excepció i sempre tanca la sessió.

    Yields:
        Sessió SQLAlchemy activa.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Proveïdors de repositoris
# ---------------------------------------------------------------------------

def get_tender_repository(db: Session) -> SqlAlchemyTenderRepository:
    """Proveeix el repositori de licitacions.

    Args:
        db: Sessió SQLAlchemy injectada per get_db().

    Returns:
        Instància de SqlAlchemyTenderRepository.
    """
    return SqlAlchemyTenderRepository(db)


def get_tender_document_repository(db: Session) -> SqlAlchemyTenderDocumentRepository:
    """Proveeix el repositori de documents adjunts de licitacions.

    Args:
        db: Sessió SQLAlchemy injectada per get_db().

    Returns:
        Instància de SqlAlchemyTenderDocumentRepository.
    """
    return SqlAlchemyTenderDocumentRepository(db)


def get_document_storage() -> LocalFileDocumentStorage:
    """Proveeix l'emmagatzematge local de PDFs.

    Returns:
        Instància de LocalFileDocumentStorage amb base_dir=downloads/.
    """
    return LocalFileDocumentStorage(base_dir=Path("downloads"))


def get_filter_repository(db: Session) -> SqlAlchemyFilterRepository:
    """Proveeix el repositori de configuracions de filtre.

    Args:
        db: Sessió SQLAlchemy injectada per get_db().

    Returns:
        Instància de SqlAlchemyFilterRepository.
    """
    return SqlAlchemyFilterRepository(db)


# ---------------------------------------------------------------------------
# Proveïdors de serveis externs
# ---------------------------------------------------------------------------

def get_api_client() -> ContractacioPublicaClient:
    """Proveeix el client HTTP de l'API de contractaciopublica.cat.

    Returns:
        Instància de ContractacioPublicaClient configurada amb Settings.
    """
    return ContractacioPublicaClient(
        base_url=_settings.pscp_portal_base_url,
        timeout=_settings.licitation_api_timeout,
        max_retries=_settings.licitation_api_max_retries,
    )


def get_nlp_analyser() -> TimbalNlpAnalyser:
    """Proveeix l'analitzador NLP basat en Timbal (model configurat via settings).

    Returns:
        Instància de TimbalNlpAnalyser configurada amb llm_model i llm_api_key.
    """
    return TimbalNlpAnalyser(model=_settings.llm_model, api_key=_settings.llm_api_key)


# ---------------------------------------------------------------------------
# Proveïdors de use cases
# ---------------------------------------------------------------------------

def get_fetch_candidates_use_case(db: Session) -> FetchCandidatesUseCase:
    """Assembla FetchCandidatesUseCase amb les seves dependències.

    Args:
        db: Sessió SQLAlchemy injectada per get_db().

    Returns:
        Instància de FetchCandidatesUseCase llesta per usar.
    """
    return FetchCandidatesUseCase(
        api=get_api_client(),
        repository=get_tender_repository(db),
    )


def get_run_pipeline_use_case(db: Session) -> RunPipelineUseCase:
    """Assembla RunPipelineUseCase amb totes les seves dependències.

    Args:
        db: Sessió SQLAlchemy injectada per get_db().

    Returns:
        Instància de RunPipelineUseCase llesta per usar.
    """
    return RunPipelineUseCase(
        fetch_candidates=get_fetch_candidates_use_case(db),
        api=get_api_client(),
        nlp=get_nlp_analyser(),
        repository=get_tender_repository(db),
        document_storage=get_document_storage(),
        document_repository=get_tender_document_repository(db),
    )
