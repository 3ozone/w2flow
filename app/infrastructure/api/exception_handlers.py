"""Gestors d'excepcions FastAPI — converteix excepcions de domini/aplicació a respostes HTTP.

Cada handler s'ha de registrar a main.py via `app.add_exception_handler()`.
L'ordre de registre no importa: FastAPI selecciona el handler més específic per classe.
"""
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def no_active_filter_config_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Converteix NoActiveFilterConfigError en una resposta HTTP 404.

    Es produeix quan el pipeline o un endpoint intenta obtenir la configuració
    activa de filtre i no n'hi ha cap a la base de dades.

    Args:
        _request: Request FastAPI (requerit per la signatura del handler).
        exc: Excepció capturada.

    Returns:
        JSONResponse amb status 404 i el missatge de l'excepció.
    """
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


def tender_api_error_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Converteix TenderApiError en una resposta HTTP 502 Bad Gateway.

    Es produeix quan la comunicació amb l'API de contractaciopublica.cat falla
    (error de xarxa, timeout, resposta no 2xx).

    Args:
        _request: Request FastAPI (requerit per la signatura del handler).
        exc: Excepció capturada amb el missatge tècnic de l'error.

    Returns:
        JSONResponse amb status 502 i el missatge de l'excepció.
    """
    logger.error("Error de l'API de contractació pública: %s", exc)
    return JSONResponse(
        status_code=502,
        content={"detail": str(exc)},
    )


def generic_error_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Converteix qualsevol excepció no controlada en una resposta HTTP 500.

    Handler de fallback — captura tot el que no ha capturat cap altre handler.
    Loga l'excepció completa per facilitar el debug, però no exposa detalls
    interns al client (seguretat).

    Args:
        _request: Request FastAPI (requerit per la signatura del handler).
        exc: Excepció no controlada.

    Returns:
        JSONResponse amb status 500 i un missatge genèric.
    """
    logger.exception("Error intern no controlat: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error intern del servidor."},
    )
