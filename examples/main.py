"""
Licitacions pipeline usando timbal Workflow + Tools + File.

Mejoras respecto a searchweb_timbal.py:
  - Workflow: pipeline explícito con pasos bien definidos
  - File.validate(): pasamos los PDFs reales a Gemini (puede leerlos)
  - Paralelo: los detalles de las 3 licitaciones se fetching a la vez
  - Tools: las funciones de la API son herramientas reutilizables
"""

import asyncio
import json
import logging
from pathlib import Path

import httpx
from timbal import Agent, Workflow
from timbal.state import get_run_context
from timbal.types.file import File

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_URL = "https://contractaciopublica.cat/portal-api"
DOWNLOAD_DIR = Path("downloads")
MAX_LICITACIONS = 3

SYSTEM_PROMPT = """Eres un experto en licitaciones públicas catalanas.
Para cada licitación recibida, con sus documentos adjuntos, formatea así:

---
📋 **[Título del contrato]**
🏛️ Órgano: [nombre del organismo]
💰 Presupuesto: [importe] €
📅 Publicación: [fecha]
🔖 Fase: [fase actual]
🔗 Expediente: [código expediente]

📁 Documentos:
  - [nombre] ([tamaño KB])
    → Resumen breve del contenido del documento

---

Al final, un resumen con el total de licitaciones y documentos analizados."""


# =============================================================================
# TOOLS — funciones de acceso a la API (reutilizables como herramientas)
# =============================================================================

def extract_documents(dades_pub: dict) -> list[dict]:
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


async def fetch_licitacions() -> list[dict]:
    """Paso 1 — Obtiene las últimas licitaciones publicadas."""
    params = {
        "page": 0,
        "inclourePublicacionsPlacsp": "false",
        "sortField": "dataUltimaPublicacio",
        "sortOrder": "desc",
    }
    async with httpx.AsyncClient(
        timeout=30, headers={"Accept": "application/json, text/plain, */*"}
    ) as client:
        r = await client.get(f"{BASE_URL}/cerca-avancada", params=params)
        r.raise_for_status()
        content = r.json().get("content", [])
        licitacions = content[:MAX_LICITACIONS]
        log.info(f"[1] Licitacions obtingudes: {len(licitacions)}")
        return licitacions


async def _fetch_and_download_one(client: httpx.AsyncClient, lic: dict) -> dict:
    """Fetching detall + descarrega docs d'una sola licitació."""
    exp_id = lic["expedientId"]
    pub_id = lic["id"]

    # Detall complet
    detail_r = await client.get(
        f"{BASE_URL}/detall-publicacio-expedient/{exp_id}/{pub_id}"
    )
    if detail_r.status_code != 200:
        log.warning(f"  SKIP {lic['titol'][:50]} — status {detail_r.status_code}")
        return {}
    detail = detail_r.json()

    dades = detail.get("dades", {})
    dades_pub = dades.get("publicacio", {}).get("dadesPublicacio", {})
    docs = extract_documents(dades_pub)
    log.info(f"  [{pub_id}] Documentos encontrados: {len(docs)}")

    # Descarrega cada document
    downloaded = []
    file_paths = []
    for doc in docs:
        doc_r = await client.get(
            f"{BASE_URL}/descarrega-document/{doc['id']}/{doc['hash']}"
        )
        if doc_r.status_code == 200:
            safe_name = doc["titol"].replace("/", "_")
            filepath = DOWNLOAD_DIR / safe_name
            filepath.write_bytes(doc_r.content)
            downloaded.append({
                "titol": doc["titol"],
                "mida_kb": round(doc.get("mida", 0) / 1024, 1),
            })
            file_paths.append(str(filepath))
            log.info(f"    ✓ {doc['titol'][:50]} ({len(doc_r.content)} bytes)")
        else:
            log.warning(f"    ✗ {doc['titol'][:40]} — {doc_r.status_code}")

    fase = (detail.get("navegacioFases") or [{}])[-1]
    return {
        "titol": lic["titol"],
        "organ": lic["organ"],
        "pressupost": lic.get("pressupostLicitacio"),
        "expedient": lic.get("codiExpedient"),
        "fase": dades.get("publicacio", {}).get("fase", {}).get("text"),
        "data_publicacio": fase.get("dataPublicacio"),
        "documents": downloaded,
        "file_paths": file_paths,
    }


async def enrich_licitacions(licitacions: list[dict]) -> dict:
    """
    Paso 2 — Fetching detalls + descarrega PDFs en PARALEL.

    asyncio.gather() llança les 3 peticions alhora en lloc de seqüencial.
    Retorna metadata enriquida + paths dels PDFs descarregats.
    """
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    log.info(f"[2] Enriquint {len(licitacions)} licitacions en paral·lel...")

    async with httpx.AsyncClient(
        timeout=60, headers={"Accept": "application/json, text/plain, */*"}
    ) as client:
        # Les 3 licitaciones es processen en paral·lel
        results = await asyncio.gather(
            *[_fetch_and_download_one(client, lic) for lic in licitacions],
            return_exceptions=False,
        )

    enriched = [r for r in results if r]
    all_file_paths = []
    for r in enriched:
        all_file_paths.extend(r.pop("file_paths", []))

    log.info(f"[2] Licitacions enriquides: {len(enriched)} | PDFs: {len(all_file_paths)}")
    return {"enriched": enriched, "file_paths": all_file_paths}


def build_prompt(data: dict) -> list:
    """
    Paso 3 — Construeix el prompt amb els PDFs reals com a File objects.

    Gràcies a File.validate(), Gemini pot LLEGIR els documents,
    no només veure el nom del fitxer.
    """
    enriched = data["enriched"]
    file_paths = data["file_paths"]

    # Adjuntem els PDFs reals — Gemini els llegirà
    pdf_files = [
        File.validate(p)
        for p in file_paths
        if Path(p).exists()
    ]
    log.info(f"[3] PDFs adjunts al prompt: {len(pdf_files)}")

    return [
        f"Analiza estas {len(enriched)} licitaciones. "
        f"Tienes adjuntos {len(pdf_files)} documentos PDF reales para leer:\n\n"
        + json.dumps(enriched, ensure_ascii=False, indent=2),
        *pdf_files,
    ]


# =============================================================================
# AGENT + WORKFLOW
# =============================================================================

agent = Agent(
    name="LicitacionsAgent",
    model="google/gemini-2.5-flash",
    system_prompt=SYSTEM_PROMPT,
)

# Pipeline explícit:
#   fetch_licitacions  ──►  enrich_licitacions  ──►  build_prompt  ──►  agent
#
# fetch i enrich s'executen seqüencialment (enrich depèn de fetch).
# Dins d'enrich, les 3 licitaciones es processen en paral·lel (asyncio.gather).

workflow = (
    Workflow(name="licitacions_pipeline")
    .step(fetch_licitacions)
    .step(
        enrich_licitacions,
        licitacions=lambda: get_run_context().step_span("fetch_licitacions").output,
    )
    .step(
        build_prompt,
        data=lambda: get_run_context().step_span("enrich_licitacions").output,
    )
    .step(
        agent,
        prompt=lambda: get_run_context().step_span("build_prompt").output,
    )
)


async def main():
    log.info("=== INICIO PIPELINE ===")
    result = await workflow().collect()
    print(result.output.collect_text())


if __name__ == "__main__":
    asyncio.run(main())
