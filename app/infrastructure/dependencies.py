"""Shared infrastructure dependencies — singleton instances for the app lifetime."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.tender_repository import TenderRepository
from app.infrastructure.services.contractacio_publica_client import (
    ContractacioPublicaClient,
)

# Built once at startup, reused across all routers
_engine = create_engine(
    settings.database_url) if settings.database_url else None
_session: Session | None = Session(_engine) if _engine else None

api_client = ContractacioPublicaClient(
    base_url=settings.pscp_portal_base_url,
    timeout=settings.licitation_api_timeout,
)

repository: TenderRepository | None = (
    TenderRepository(session=_session) if _session else None
)

document_storage: DocumentRepository | None = (
    DocumentRepository(session=_session, base_dir=settings.download_dir)
    if _session else None
)
