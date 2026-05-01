"""FastAPI router for scored tenders endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.application.ports.tender_repository_port import TenderRepositoryPort
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
