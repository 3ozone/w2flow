"""Router FastAPI per a la consulta de licitacions — GET /api/v1/tenders.

Endpoint:
  GET /api/v1/tenders → llista totes les licitacions persistides a la BD

La consulta es delega a SqlAlchemyTenderRepository via get_tender_repository().
"""
from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.dependencies import get_db, get_tender_repository

router = APIRouter(prefix="/api/v1/tenders", tags=["tenders"])


@router.get("", response_model=None)
def list_tenders(db: Session = Depends(get_db)) -> list[dict]:
    """Retorna totes les licitacions persistides a la base de dades.

    Les licitacions s'ordenen per data_limit descendent (les més recents primer).
    Només s'inclouen licitacions ja processades pel pipeline (no les candidates).

    Args:
        db: Sessió SQLAlchemy injectada per FastAPI via get_db().

    Returns:
        Llista de licitacions serialitzades com a diccionaris.
        Llista buida si no hi ha licitacions a la BD.
    """
    repo = get_tender_repository(db)
    tenders = repo.list_all()
    return [asdict(t) for t in tenders]
