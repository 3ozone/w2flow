"""FastAPI router for scored tenders endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response

from app.application.ports.tender_repository_port import TenderRepositoryPort
from app.infrastructure.api.v1.schemas.document_schema import DocumentSchema
from app.infrastructure.api.v1.schemas.tender_schema import TenderSchema

router = APIRouter(tags=["tenders"])

# Injected at app startup — overridden in tests
_repository: TenderRepositoryPort | None = None


@router.get("/tenders", response_model=list[TenderSchema])
async def list_tenders(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1),
) -> list[TenderSchema]:
    """Return a paginated list of scored tenders."""
    scored = await _repository.list_scored(page=page, size=size)
    return [TenderSchema.from_domain(st) for st in scored]


@router.get("/tenders/{tender_id}", response_model=TenderSchema)
async def get_tender(tender_id: str) -> TenderSchema:
    """Return a single scored tender by expedient_id, or 404 if not found."""
    scored = await _repository.list_scored(page=0, size=10_000)
    for st in scored:
        if st.tender.expedient_id == tender_id:
            return TenderSchema.from_domain(st)
    raise HTTPException(
        status_code=404, detail=f"Tender '{tender_id}' not found")


@router.get("/tenders/{tender_id}/documents", response_model=list[DocumentSchema])
async def list_tender_documents(tender_id: str) -> list[DocumentSchema]:
    """Return all documents for a tender, or 404 if the tender does not exist."""
    scored = await _repository.list_scored(page=0, size=10_000)
    exists = any(st.tender.expedient_id == tender_id for st in scored)
    if not exists:
        raise HTTPException(
            status_code=404, detail=f"Tender '{tender_id}' not found")
    documents = await _repository.list_documents(tender_id)
    return [DocumentSchema.from_domain(doc) for doc in documents]


@router.get("/tenders/{tender_id}/documents/{doc_id}/download")
async def download_tender_document(tender_id: str, doc_id: int) -> FileResponse:
    """Download the PDF file for a specific document, or 404 if not found."""
    scored = await _repository.list_scored(page=0, size=10_000)
    exists = any(st.tender.expedient_id == tender_id for st in scored)
    if not exists:
        raise HTTPException(
            status_code=404, detail=f"Tender '{tender_id}' not found")
    documents = await _repository.list_documents(tender_id)
    doc = next((d for d in documents if d.doc_id == doc_id), None)
    if doc is None:
        raise HTTPException(
            status_code=404, detail=f"Document '{doc_id}' not found")
    return FileResponse(
        path=doc.file_path,
        media_type="application/pdf",
        filename=doc.titol,
    )


@router.delete("/tenders/{tender_id}", status_code=204)
async def delete_tender(tender_id: str) -> Response:
    """Delete a tender and all its documents and scores, or 404 if not found."""
    scored = await _repository.list_scored(page=0, size=10_000)
    exists = any(st.tender.expedient_id == tender_id for st in scored)
    if not exists:
        raise HTTPException(
            status_code=404, detail=f"Tender '{tender_id}' not found")
    await _repository.delete(tender_id)
    return Response(status_code=204)
