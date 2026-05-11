"""Router FastAPI per al pipeline de licitacions — POST /api/v1/pipeline/run.

Responsabilitat única: rebre el request HTTP, obtenir la FilterConfig activa,
delegar l'execució al RunPipelineUseCase i retornar el ReportDTO serialitzat.
Tota la lògica de negoci viu als use cases i al domini.
"""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.dtos.report_dto import ReportDTO
from app.infrastructure.dependencies import get_db, get_filter_repository, get_run_pipeline_use_case

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])


@router.post("/run", response_model=None)
def run_pipeline(db: Session = Depends(get_db)) -> ReportDTO:
    """Executa el pipeline complet de cerca, anàlisi i puntuació de licitacions.

    Obté la FilterConfig activa de la base de dades, llança el pipeline complet
    (fetch → documents → NLP → score) i retorna el report amb totes les
    licitacions puntuades.

    Args:
        db: Sessió SQLAlchemy injectada per FastAPI via get_db().

    Returns:
        ReportDTO amb la llista de licitacions puntuades i el resum de resultats.

    Raises:
        NoActiveFilterConfigError: Si no hi ha cap FilterConfig activa (→ HTTP 404).
        TenderApiError: Si la comunicació amb l'API externa falla (→ HTTP 502).
    """
    filter_repo = get_filter_repository(db)
    config = filter_repo.get_active()

    use_case = get_run_pipeline_use_case(db)
    return use_case.execute(config=config, today=date.today())
