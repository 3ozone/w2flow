"""HTTP client for the contractaciopublica.cat portal API."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx

from app.application.ports.licitacion_api_port import LicitationApiPort
from app.domain.exceptions.download_error import DownloadError
from app.domain.value_objects.filter_config import FilterConfig

log = logging.getLogger(__name__)


class ContractacioPublicaClient(LicitationApiPort):
    """Implements LicitationApiPort using httpx against contractaciopublica.cat."""

    def __init__(self, base_url: str, timeout: int = 30) -> None:
        self._base_url = base_url.rstrip("/")
        self._http_client = httpx.AsyncClient(timeout=timeout)

    @asynccontextmanager
    async def _http_errors(self, context: str) -> AsyncIterator[None]:
        """Wrap httpx errors into DownloadError with context info."""
        try:
            yield
        except httpx.HTTPError as exc:
            raise DownloadError(f"{context}: {exc}") from exc

    async def fetch_page(self, filter_config: FilterConfig, page: int) -> list[dict]:
        """Fetch a single page of tender summaries from the API."""
        params = {
            "tipusExpedient": filter_config.tipus_expedient,
            "faseVigent": filter_config.fase_vigent,
            "page": page,
            "size": 20,
            "sortField": "dataUltimaPublicacio",
            "sortOrder": "desc",
        }
        log.debug("[HTTP] GET cerca-avancada page=%d params=%s", page, params)
        async with self._http_errors(f"fetch_page(page={page})"):
            response = await self._http_client.get(
                f"{self._base_url}/cerca-avancada",
                params=params,
            )
            response.raise_for_status()
            result = response.json().get("content", [])
            log.debug("[HTTP] cerca-avancada → %d items", len(result))
            return result

    async def fetch_detail(self, expedient_id: str, publicacio_id: int) -> dict:
        """Fetch full detail for a single tender."""
        async with self._http_errors(f"fetch_detail({expedient_id}/{publicacio_id})"):
            response = await self._http_client.get(
                f"{self._base_url}/detall-publicacio-expedient"
                f"/{expedient_id}/{publicacio_id}",
            )
            response.raise_for_status()
            return response.json()

    async def fetch_documents(self, expedient_id: str, publicacio_id: int) -> list[dict]:
        """Return all downloadable documents for a tender (recursive DFS over dades)."""
        log.info("[HTTP] GET detall-publicacio-expedient/%s/%s (docs)",
                 expedient_id, publicacio_id)
        async with self._http_errors(f"fetch_documents({expedient_id}/{publicacio_id})"):
            response = await self._http_client.get(
                f"{self._base_url}/detall-publicacio-expedient"
                f"/{expedient_id}/{publicacio_id}",
            )
            response.raise_for_status()
            data = response.json()

        dades = data.get("dades") or {}
        docs = self._extract_documents(dades)
        log.info("[HTTP] fetch_documents → %d docs found for %s",
                 len(docs), expedient_id)
        return docs

    @staticmethod
    def _extract_documents(node: object) -> list[dict]:
        """Recursively find document nodes: dicts with int id, titol and hash."""
        found: list[dict] = []
        if isinstance(node, dict):
            if (
                isinstance(node.get("id"), int)
                and isinstance(node.get("titol"), str)
                and isinstance(node.get("hash"), str)
            ):
                found.append(node)
            else:
                for value in node.values():
                    found.extend(
                        ContractacioPublicaClient._extract_documents(value))
        elif isinstance(node, list):
            for item in node:
                found.extend(
                    ContractacioPublicaClient._extract_documents(item))
        return found

    async def download_document(self, doc_id: int, doc_hash: str) -> bytes:
        """Download the raw PDF bytes for a document."""
        log.info("[HTTP] GET descarrega-document/%d/%s", doc_id, doc_hash)
        async with self._http_errors(f"download_document(doc_id={doc_id})"):
            response = await self._http_client.get(
                f"{self._base_url}/descarrega-document/{doc_id}/{doc_hash}",
            )
            response.raise_for_status()
            size_kb = len(response.content) / 1024
            log.info("[HTTP] download_document/%d → %.1f KB", doc_id, size_kb)
            return response.content
