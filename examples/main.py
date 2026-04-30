"""Descarga y procesa licitaciones públicas catalanas usando la API de Contractació Pública."""

import json
import asyncio
import logging
from pathlib import Path
import httpx
# from abc import ABC, abstractmethod

from timbal import Agent, Workflow
from timbal.state import get_run_context
from timbal.types.file import File

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Eres un experto en licitaciones públicas catalanas trabajando para una empresa de ingeniería y construcción.
Para cada licitación recibida, con sus documentos adjuntos, formatea así:

---
📋 **[Título del contrato]**
🏛️ Órgano: [nombre del organismo]
💰 Presupuesto: [importe] €
📅 Publicación: [fecha]
🔖 Fase: [fase actual]
🔗 Expediente: [código expediente]
🎯 **Puntuación: [score.total]/70 — [score.recomanacio]**
   - Presupuesto: [score.detall.pressupost] pts
   - Sector relevante: [score.detall.sector_positiu] pts
   - Penalizaciones IT/software: [score.detall.sector_negatiu] pts
   - Procedimiento abierto: [score.detall.procediment_obert] pts
   - Subcontratación permitida: [score.detall.subcontractació] pts
   - Palabras clave encontradas: [score.paraules_clau_trobades]

📁 Documentos:
  - [nombre] ([tamaño KB])
    → Resumen breve del contenido del documento

---

Al final, ordena las licitaciones por puntuación (mayor a menor) y añade un resumen ejecutivo de cuáles son más interesantes para una empresa de ingeniería/construcción."""


class GetTender():
    """class to extract documents"""

    def __init__(self):
        self.base_url = "https://contractaciopublica.cat/portal-api"
        self.params = {
            "page": 0,
            "inclourePublicacionsPlacsp": "false",
            "sortField": "dataUltimaPublicacio",
            "sortOrder": "desc",
        }
        self.download_dir = Path("downloads")
        self.max_licitacions = 10
        self.download_dir = Path("downloads")
        self.downloaded = []
        self.detail = {}

    def extract_documents(self, dades_pub: dict) -> list[dict]:
        """Extrae todos los documentos descargables de dadesPublicacio."""
        docs = []
        pending = [dades_pub]
        while pending:
            node = pending.pop()
            if isinstance(node, dict):
                if "titol" in node and "hash" in node and isinstance(node.get("id"), int):
                    docs.append(node)
                else:
                    pending.extend(node.values())
            elif isinstance(node, list):
                pending.extend(node)
        return docs

    async def get_tender(self) -> list[dict]:
        """Extract documents from dades."""
        async with httpx.AsyncClient(timeout=30, headers={"Accept": "application/json, */*"}) as client:
            r = await client.get(f"{self.base_url}/cerca-avancada",
                                 params=self.params)
            r.raise_for_status()
            content = r.json().get("content", [])
            licitacions = content[:self.max_licitacions]
            log.info("[1] Licitacions obtingudes: %s", len(licitacions))
            return licitacions

    async def extract_documents_from_tender(self, client: httpx.AsyncClient, lic: dict) -> dict | None:
        """Extract documents from a single licitació."""
        exp_id = lic["expedientId"]
        pub_id = lic["id"]

        # Detall complet
        detail_r = await client.get(
            f"{self.base_url}/detall-publicacio-expedient/{exp_id}/{pub_id}")

        if detail_r.status_code != 200:
            log.warning(
                "  SKIP {lic['titol'][:50]} — status %s", detail_r.status_code)
            return {}

        detail = detail_r.json()

        dades = detail.get("dades", {})
        docs = self.extract_documents(dades)
        log.info("[%s] Documentos encontrados: %s", pub_id, len(docs))
        return {
            "licitacio": lic,
            "documents": docs,
            "detail": detail,
        }

    async def download_document(self, client: httpx.AsyncClient, doc: dict, lic: dict, detail: dict) -> dict | None:
        """Download a document by its id and hash."""
        lic_dir = self.download_dir / str(lic["expedientId"])
        lic_dir.mkdir(parents=True, exist_ok=True)

        doc_r = await client.get(f"{self.base_url}/descarrega-document/{doc['id']}/{doc['hash']}")

        file_path = None

        if doc_r.status_code == 200:
            safe_name = doc["titol"].replace("/", "_")
            filepath = lic_dir / safe_name
            filepath.write_bytes(doc_r.content)
            file_path = str(filepath)
            log.info("✓ %s (%s bytes)", doc['titol'][:50], len(doc_r.content))
        else:
            log.warning("✗ %s — %s", doc['titol'][:40], doc_r.status_code)

        fase = (detail.get("navegacioFases") or [{}])[-1]
        dades = detail.get("dades", {})

        return {
            "titol": lic["titol"],
            "organ": lic["organ"],
            "pressupost": lic.get("pressupostLicitacio"),
            "expedient": lic.get("codiExpedient"),
            "fase": dades.get("publicacio", {}).get("fase", {}).get("text"),
            "data_publicacio": fase.get("dataPublicacio"),
            "document": doc["titol"],
            "mida_kb": round(doc.get("mida", 0) / 1024, 1),
            "file_path": file_path,
        }


async def main():
    """Main workflow."""
    print("Iniciando workflow...")
    getter = GetTender()
    licitacions = await getter.get_tender()

    async with httpx.AsyncClient(
        timeout=30, headers={"Accept": "application/json, */*"}
    ) as cli:
        # Obtém detall + documents de totes les licitacions en paral·lel
        results = await asyncio.gather(
            *[getter.extract_documents_from_tender(cli, lic) for lic in licitacions]
        )

        # Filtra resultats vàlids (descarta licitacions amb error HTTP)
        valid_results = [r for r in results if r and r.get("documents") is not None]

        # Descarrega tots els documents de totes les licitacions en paral·lel
        all_downloads = await asyncio.gather(
            *[
                getter.download_document(cli, doc, r["licitacio"], r["detail"])
                for r in valid_results
                for doc in r["documents"]
            ]
        )

    print(json.dumps(all_downloads, indent=2, ensure_ascii=False))


asyncio.run(main())
