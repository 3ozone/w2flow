"""FastAPI router for health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.infrastructure import dependencies

router = APIRouter(tags=["health"])


def _check_db() -> str:
    """Return 'ok' if the DB session responds, 'error' otherwise."""
    session = dependencies._session
    if session is None:
        return "error"
    try:
        from sqlalchemy import text
        session.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


class _HealthResponse(BaseModel):
    status: str
    db: str


@router.get("/health", response_model=_HealthResponse)
async def get_health() -> _HealthResponse:
    """Return service health status. Always returns 200."""
    db_status = _check_db()
    overall = "ok" if db_status == "ok" else "degraded"
    return _HealthResponse(status=overall, db=db_status)
