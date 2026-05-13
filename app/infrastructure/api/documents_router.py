"""Router FastAPI per a la gestió de documents adjunts de licitacions (RF-09, J.7).

Endpoints:
  GET    /documents/{expedient_id}/{filename}/download  → serveix el PDF com a FileResponse
  DELETE /documents/{expedient_id}/{filename}           → esborra de disc i de BD
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.infrastructure.dependencies import (
    get_db,
    get_document_storage,
    get_tender_document_repository,
)
from app.infrastructure.services.local_file_document_storage import LocalFileDocumentStorage

router = APIRouter(prefix="/documents", tags=["documents"])

_DOWNLOADS_DIR = Path("downloads")


@router.get("/{expedient_id}/{filename}/download")
def download_document(
    expedient_id: str,
    filename: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    """Serveix el PDF d'un document adjunt com a FileResponse (RF-09).

    Args:
        expedient_id: UUID de la licitació.
        filename:     Nom del fitxer PDF.
        db:           Sessió SQLAlchemy (necessària per verificar existència a BD).

    Returns:
        FileResponse amb el contingut del PDF.

    Raises:
        HTTPException 404: Si el document no existeix a la BD o al disc.
    """
    doc_repo = get_tender_document_repository(db)
    docs = doc_repo.list_by_expedient(expedient_id)
    matched = next((d for d in docs if d.filename == filename), None)
    if matched is None:
        raise HTTPException(status_code=404, detail="Document no trobat.")

    filepath = Path(matched.filepath)
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Fitxer no trobat al disc.")

    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=filename,
    )


@router.delete("/{expedient_id}/{filename}")
def delete_document(
    expedient_id: str,
    filename: str,
    db: Session = Depends(get_db),
    storage: LocalFileDocumentStorage = Depends(get_document_storage),
) -> JSONResponse:
    """Esborra un document adjunt de disc i de la base de dades (RF-09).

    Args:
        expedient_id: UUID de la licitació.
        filename:     Nom del fitxer PDF a esborrar.
        db:           Sessió SQLAlchemy.
        storage:      Servei d'emmagatzematge local de fitxers.

    Returns:
        JSONResponse amb missatge de confirmació.

    Raises:
        HTTPException 404: Si el document no existeix a la BD.
    """
    doc_repo = get_tender_document_repository(db)
    docs = doc_repo.list_by_expedient(expedient_id)
    matched = next((d for d in docs if d.filename == filename), None)
    if matched is None:
        raise HTTPException(status_code=404, detail="Document no trobat.")

    # Esborrar del disc (ignora si el fitxer ja no hi és)
    storage.delete(expedient_id=expedient_id, filename=filename)

    # Esborrar de la BD
    from app.infrastructure.models.tender_document_model import TenderDocumentModel
    db.query(TenderDocumentModel).filter(
        TenderDocumentModel.expedient_id == expedient_id,
        TenderDocumentModel.filename == filename,
    ).delete()

    return JSONResponse(content={"detail": f"Document '{filename}' esborrat correctament."})
