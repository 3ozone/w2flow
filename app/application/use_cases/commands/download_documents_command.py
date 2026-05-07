"""DownloadDocumentsCommand and its handler."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.application.ports.document_storage_port import DocumentStoragePort
from app.application.ports.licitacion_api_port import LicitationApiPort
from app.domain.entities.document import Document
from app.domain.entities.tender import Tender
from app.domain.value_objects.document_type import DocumentType

log = logging.getLogger(__name__)


@dataclass
class DownloadDocumentsCommand:
    """Command to download and store all valid documents for a tender."""

    tender: Tender


class DownloadDocumentsCommandHandler:
    """Downloads PDFs for a tender, skips UNKNOWN types and already-stored docs."""

    def __init__(self, api: LicitationApiPort, storage: DocumentStoragePort) -> None:
        self._api = api
        self._storage = storage

    async def handle(self, command: DownloadDocumentsCommand) -> list[tuple[Document, bytes | None]]:
        """Fetch document metadata, download valid types and persist them.

        Returns a list of (Document, pdf_bytes) tuples. For already-stored
        documents, pdf_bytes is None. For newly downloaded ones, pdf_bytes
        contains the raw PDF content so callers can extract text without
        re-reading from disk.
        """
        tender = command.tender
        raw_docs = await self._api.fetch_documents(
            tender.expedient_id, tender.publicacio_id
        )

        documents: list[tuple[Document, bytes | None]] = []

        for raw in raw_docs:
            doc_id: int = raw["id"]
            titol: str = raw["titol"]
            doc_hash: str = raw.get("hash", "")
            mida_kb: float = float(raw.get("midaKb", 0.0))
            doc_type = DocumentType.from_title(titol)

            if doc_type == DocumentType.UNKNOWN:
                log.debug("[DOCS] Skipping UNKNOWN document type: %s", titol)
                continue

            if await self._storage.exists(tender.expedient_id, doc_id):
                file_path = await self._storage.get_path(tender.expedient_id, doc_id)
                pdf_bytes: bytes | None = None
                log.debug("[DOCS] Already stored (skip download): %s", titol)
            else:
                pdf_bytes = await self._api.download_document(doc_id, doc_hash)
                doc = Document(
                    expedient_id=tender.expedient_id,
                    doc_id=doc_id,
                    titol=titol,
                    hash=doc_hash,
                    mida_kb=mida_kb,
                    file_path="",
                    type=doc_type,
                )
                file_path = await self._storage.save(doc, pdf_bytes)
                log.info("[DOCS] Downloaded and stored: %s -> %s",
                         titol, file_path)

            documents.append((
                Document(
                    expedient_id=tender.expedient_id,
                    doc_id=doc_id,
                    titol=titol,
                    hash=doc_hash,
                    mida_kb=mida_kb,
                    file_path=file_path,
                    type=doc_type,
                ),
                pdf_bytes,
            ))

        return documents
