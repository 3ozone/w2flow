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
import pymupdf
from timbal import Agent, Workflow
from timbal.state import get_run_context
from timbal.types.file import File

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_URL = "https://contractaciopublica.cat/portal-api"
DOWNLOAD_DIR = Path("downloads")
MAX_LICITACIONS = 10

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
        log.warning(
            f"  SKIP {lic['titol'][:50]} — status {detail_r.status_code}")
        return {}
    detail = detail_r.json()

    dades = detail.get("dades", {})
    # Cerca recursiva sobre tot dades: troba documents tant a dadesPublicacio
    # com a documentFormalitzacio (i qualsevol altra clau futura).
    docs = extract_documents(dades)
    log.info(f"  [{pub_id}] Documentos encontrados: {len(docs)}")

    # Sub-carpeta exclusiva per a aquesta licitació
    lic_dir = DOWNLOAD_DIR / str(exp_id)
    lic_dir.mkdir(parents=True, exist_ok=True)

    # Descarrega cada document
    downloaded = []
    file_paths = []
    for doc in docs:
        doc_r = await client.get(
            f"{BASE_URL}/descarrega-document/{doc['id']}/{doc['hash']}"
        )
        if doc_r.status_code == 200:
            safe_name = doc["titol"].replace("/", "_")
            filepath = lic_dir / safe_name
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
    total_pdfs = sum(len(r.get("file_paths", [])) for r in enriched)
    log.info(
        f"[2] Licitacions enriquides: {len(enriched)} | PDFs: {total_pdfs}")
    return {"enriched": enriched}


# =============================================================================
# SCORING — puntuació per a empresa d'enginyeria/construcció (màx 70 pts)
# =============================================================================

SCORE_CONFIG = {
    "sector_positiu": [
        "obres", "construcció", "infraestructura", "reforma", "rehabilitació",
        "urbanisme", "enginyeria", "instal·lació", "instal.lació", "maquinari",
        "manteniment", "obra civil", "edificació", "pavimentació", "canalització",
        "xarxa", "electricitat", "fontaneria", "climatització", "ascensor",
        "estructura", "fonamentació", "maquinaria escènica", "maquinaria",
    ],
    "sector_negatiu": [
        "software", "saas", "plataforma digital", "aplicació web",
        "recursos humans", "nòmina", "gestió de persones", "assegurança",
        "servei jurídic", "auditoria financera", "consultoria de gestió",
    ],
}


def _score_one(lic: dict) -> dict:
    """Puntua una licitació a partir del text dels seus PDFs."""
    # Texto base: título + texto de todos los PDFs de la licitación
    text = lic.get("titol", "").lower() + " "
    for pdf_path in lic.get("file_paths", []):
        p = Path(pdf_path)
        if p.exists() and p.suffix.lower() == ".pdf":
            try:
                doc = pymupdf.open(str(p))
                for page in doc:
                    text += page.get_text().lower()
            except Exception:
                pass

    # Criteri 1: pressupost (0-25 pts)
    pressupost = lic.get("pressupost") or 0
    if pressupost >= 1_000_000:
        pts_pressupost = 25
    elif pressupost >= 500_000:
        pts_pressupost = 20
    elif pressupost >= 100_000:
        pts_pressupost = 10
    else:
        pts_pressupost = 5

    # Criteri 2: sector positiu (0-30 pts, +5 per paraula clau, màx 30)
    hits_pos = [kw for kw in SCORE_CONFIG["sector_positiu"] if kw in text]
    pts_sector_pos = min(len(hits_pos) * 5, 30)

    # Criteri 3: sector negatiu (penalització -10 per paraula clau)
    hits_neg = [kw for kw in SCORE_CONFIG["sector_negatiu"] if kw in text]
    pts_sector_neg = len(hits_neg) * -10

    # Criteri 4: procediment obert (+10 pts)
    pts_procediment = 10 if "procediment obert" in text else 0

    # Criteri 5: subcontractació permesa (+5 pts)
    pts_subcontract = 5 if "subcontract" in text else 0

    total = max(0, pts_pressupost + pts_sector_pos +
                pts_sector_neg + pts_procediment + pts_subcontract)
    recomanacio = "✅ RECOMANADA" if total >= 50 else (
        "⚠️ A VALORAR" if total >= 25 else "❌ NO RECOMANADA")

    log.info(
        f"  [{lic.get('expedient', '?')}] Puntuació: {total}/70 — {recomanacio}"
        f" (pressupost+{pts_pressupost} sector+{pts_sector_pos} neg{pts_sector_neg})"
    )
    return {
        "total": total,
        "recomanacio": recomanacio,
        "detall": {
            "pressupost": pts_pressupost,
            "sector_positiu": pts_sector_pos,
            "sector_negatiu": pts_sector_neg,
            "procediment_obert": pts_procediment,
            "subcontractació": pts_subcontract,
        },
        "paraules_clau_trobades": hits_pos,
        "penalitzacions": hits_neg,
    }


def score_licitacions(data: dict) -> dict:
    """
    Paso 3 — Puntua cada licitació llegint el text dels seus PDFs.

    Criteris (màx 70 pts):
      - Pressupost         0-25 pts  (>1M=25, >500K=20, >100K=10, resta=5)
      - Sector positiu     0-30 pts  (+5 per paraula clau eng/construcció, màx 30)
      - Sector negatiu     0   pts   (-10 per paraula clau IT/software)
      - Procediment obert    10 pts
      - Subcontractació       5 pts
    """
    enriched = data["enriched"]
    log.info(f"[3] Puntuant {len(enriched)} licitacions...")

    all_file_paths = []
    for lic in enriched:
        lic["score"] = _score_one(lic)
        all_file_paths.extend(lic.get("file_paths", []))

    return {"enriched": enriched, "all_file_paths": all_file_paths}


def build_prompt(data: dict) -> list:
    """
    Paso 4 — Construeix el prompt amb puntuació i PDFs reals com a File objects.

    Gràcies a File.validate(), Gemini pot LLEGIR els documents directament.
    """
    enriched = data["enriched"]
    all_file_paths = data["all_file_paths"]

    # Serialitzem sense file_paths (innecessari al JSON del prompt)
    lic_summary = [
        {k: v for k, v in lic.items() if k != "file_paths"}
        for lic in enriched
    ]

    # Adjuntem els PDFs reals — Gemini els llegirà
    pdf_files = [
        File.validate(p)
        for p in all_file_paths
        if Path(p).exists() and p.endswith(".pdf")
    ]
    log.info(f"[4] PDFs adjunts al prompt: {len(pdf_files)}")

    return [
        f"Analiza estas {len(enriched)} licitaciones para nuestra empresa de ingeniería/construcción. "
        f"Tienes adjuntos {len(pdf_files)} documentos PDF reales para leer. "
        "Usa la puntuación precalculada (campo 'score') y los documentos para justificar la recomendación:\n\n"
        + json.dumps(lic_summary, ensure_ascii=False, indent=2),
        *pdf_files,
    ]


# =============================================================================
# AGENT + WORKFLOW
# =============================================================================

_agent = Agent(
    name="LicitacionsAgent",
    model="google/gemini-2.5-flash",
    system_prompt=SYSTEM_PROMPT,
)


# Pipeline explícit:
#   fetch_licitacions
#       ──► enrich_licitacions      (parallel: 3 licitacions alhora)
#               ──► score_licitacions   (llegeix PDFs, calcula puntuació)
#                       ──► build_prompt   (retorna la llista per a l'agent)
#
# L'agent es crida directament a main() fora del context del workflow
# per evitar problemes de context nesting de timbal.

workflow = (
    Workflow(name="licitacions_pipeline")
    .step(fetch_licitacions)
    .step(
        enrich_licitacions,
        licitacions=lambda: get_run_context().step_span("fetch_licitacions").output,
    )
    .step(
        score_licitacions,
        data=lambda: get_run_context().step_span("enrich_licitacions").output,
    )
    .step(
        build_prompt,
        data=lambda: get_run_context().step_span("score_licitacions").output,
    )
)


async def main():
    """Executa el workflow i després crida l'agent amb el prompt construït."""
    log.info("=== INICIO PIPELINE ===")

    # Pas 1-4: descarrega, enriquiment, scoring i construcció del prompt
    pipeline_result = await workflow().collect()
    prompt_parts = pipeline_result.output

    if prompt_parts is None:
        log.error("El pipeline no ha retornat cap resultat.")
        return

    # Pas 5: l'agent analitza les licitacions + PDFs
    log.info("[5] Cridant l'agent Gemini...")
    agent_result = await _agent(prompt=prompt_parts).collect()

    if agent_result.output is None:
        log.error("L'agent no ha retornat resposta. Comprova la GEMINI_API_KEY.")
        return

    print(agent_result.output.collect_text())


if __name__ == "__main__":
    asyncio.run(main())
