"""Router FastAPI per a la gestió de configuracions de filtre — /api/v1/filters.

Endpoints:
  GET  /api/v1/filters        → llista totes les configuracions (históric)
  GET  /api/v1/filters/active → retorna la configuració activa
  POST /api/v1/filters        → crea una nova configuració i la marca com a activa

Tota la persistència es delega a SqlAlchemyFilterRepository via get_filter_repository().
"""
import json
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.domain.value_objects.filter_config import FilterConfig
from app.infrastructure.dependencies import get_db, get_filter_repository

router = APIRouter(prefix="/api/v1/filters", tags=["filters"])


# ---------------------------------------------------------------------------
# Schema d'entrada (Pydantic) — representa el body del POST
# ---------------------------------------------------------------------------

class FilterConfigRequest(BaseModel):
    """Body del request per crear una nova configuració de filtre.

    Attributes:
        tipus_expedient:         Tipus d'expedient (obligatori).
        fase_vigent:             Fase vigent (obligatori).
        ambit:                   Àmbit geogràfic (opcional).
        tipus_contracte:         Tipus de contracte (opcional).
        procediment_adjudicacio: Procediment d'adjudicació (opcional).
        cpv_codes:               Codis CPV permesos (buit = sense filtre).
        pressupost_maxim:        Pressupost màxim en EUR (0.0 = sense límit).
        nuts_codes:              Codis NUTS permesos (buit = sense filtre).
        classifications:         Grups empresarials permesos (buit = sense filtre).
        durada_minima_dies:      Durada mínima en dies (0 = sense límit).
        durada_maxima_dies:      Durada màxima en dies (0 = sense límit).
        max_licitacions:         Nombre màxim de licitacions a processar (1–100, per defecte 20).
    """

    tipus_expedient: int
    fase_vigent: int = 30
    ambit: int | None = None
    tipus_contracte: int | None = None
    procediment_adjudicacio: int | None = None
    cpv_codes: list[str] = []
    pressupost_maxim: float = 0.0
    nuts_codes: list[str] = []
    classifications: list[str] = []
    durada_minima_dies: int = 0
    durada_maxima_dies: int = 0
    max_licitacions: int = Field(default=20, ge=1, le=100)

    @field_validator("classifications", "cpv_codes", "nuts_codes", mode="before")
    @classmethod
    def _parse_json_string(cls, value: Any) -> Any:
        """Parseja strings JSON a llista per evitar iteració caràcter a caràcter.

        Pydantic v2 en mode lenient accepta strings iterables per a list[str],
        convertint '[]' en ['[', ']']. Aquest validator ho corregeix.
        """
        if isinstance(value, str):
            return json.loads(value)
        return value


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=None)
def list_filters(db: Session = Depends(get_db)) -> list[dict]:
    """Retorna l'historial complet de configuracions de filtre ordenat per data.

    Args:
        db: Sessió SQLAlchemy injectada per FastAPI via get_db().

    Returns:
        Llista de FilterConfig serialitzades com a diccionaris, de més recent a més antic.
    """
    repo = get_filter_repository(db)
    configs = repo.list_all()
    return [asdict(c) for c in configs]


@router.get("/active", response_model=None)
def get_active_filter(db: Session = Depends(get_db)) -> dict:
    """Retorna la configuració de filtre activa.

    Args:
        db: Sessió SQLAlchemy injectada per FastAPI via get_db().

    Returns:
        FilterConfig activa serialitzada com a diccionari.

    Raises:
        NoActiveFilterConfigError: Si no hi ha cap configuració activa (→ HTTP 404).
    """
    repo = get_filter_repository(db)
    config = repo.get_active()
    return asdict(config)


@router.post("", status_code=201, response_model=None)
def create_filter(body: FilterConfigRequest, db: Session = Depends(get_db)) -> dict:
    """Crea una nova configuració de filtre i la marca com a activa.

    Desactiva automàticament qualsevol configuració activa anterior.

    Args:
        body: Dades de la nova configuració (validades per Pydantic).
        db:   Sessió SQLAlchemy injectada per FastAPI via get_db().

    Returns:
        La nova FilterConfig serialitzada com a diccionari.
    """
    config = FilterConfig(
        tipus_expedient=body.tipus_expedient,
        fase_vigent=body.fase_vigent,
        ambit=body.ambit,
        tipus_contracte=body.tipus_contracte,
        procediment_adjudicacio=body.procediment_adjudicacio,
        cpv_codes=tuple(body.cpv_codes),
        pressupost_maxim=body.pressupost_maxim,
        nuts_codes=tuple(body.nuts_codes),
        classifications=tuple(body.classifications),
        durada_minima_dies=body.durada_minima_dies,
        durada_maxima_dies=body.durada_maxima_dies,
        max_licitacions=body.max_licitacions,
    )
    repo = get_filter_repository(db)
    repo.save(config)
    return asdict(config)
