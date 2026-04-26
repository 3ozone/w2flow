import json
import logging
from pathlib import Path

import httpx
from timbal import Agent

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_URL = "https://contractaciopublica.cat/portal-api"
DOWNLOAD_DIR = Path("downloads")
MAX_LICITACIONS = 3

SEARCH_PARAMS = {
    "page": 0,
    "inclourePublicacionsPlacsp": "false",
    "sortField": "dataUltimaPublicacio",
    "sortOrder": "desc",
}

SYSTEM_PROMPT = """Eres un experto en licitaciones públicas catalanas.
Para cada licitación recibida, formatea así:

---
📋 **[Título del contrato]**
🏛️ Órgano: [nombre del organismo]
💰 Presupuesto: [importe] €
📅 Publicación: [fecha]
🔖 Fase: [fase actual]
🔗 Expediente: [código expediente]

📁 Documentos descargados:
  - [nombre documento] ([tipo, tamaño en KB])
    → Descripción breve basada en el nombre y tipo de documento

---

Al final, un resumen con el total de licitaciones y documentos descargados."""

agent = Agent(
    name="LicitacionsAgent",
    model="google/gemini-2.5-flash",
    system_prompt=SYSTEM_PROMPT,
)


def extract_documents(data: dict | list, docs: list | None = None) -> list:
    """Recursively extract all document objects from the detail JSON."""
    if docs is None:
        docs = []
    if isinstance(data, dict):
        if "titol" in data and "hash" in data and isinstance(data.get("id"), int):
            docs.append(data)
        else:
            for value in data.values():
                extract_documents(value, docs)
    elif isinstance(data, list):
        for item in data:
            extract_documents(item, docs)
    return docs


async def main():
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    log.info("=== INICIO ===")
    log.info(f"Directorio de descarga: {DOWNLOAD_DIR.resolve()}")

    # header => "Accept": "application/json, text/plain, */*" le decimos que queremos json
    with httpx.Client(timeout=30, headers={"Accept": "application/json, text/plain, */*"}) as client:
        # 1. Fetch licitacions list
        log.info(f"[1] GET {BASE_URL}/cerca-avancada params={SEARCH_PARAMS}")
        response = client.get(
            f"{BASE_URL}/cerca-avancada", params=SEARCH_PARAMS)
        log.info(f"    Status: {response.status_code}")
        response.raise_for_status()
        all_content = response.json().get("content", [])
        licitacions = all_content[:MAX_LICITACIONS]
        log.info(
            f"    Total en página: {len(all_content)} | Procesando: {len(licitacions)}")

        enriched = []
        for i, lic in enumerate(licitacions):
            log.info(
                f"\n--- Licitació {i+1}/{len(licitacions)}: {lic.get('titol', '')[:60]} ---")
            log.info(f"    expedientId={lic['expedientId']}  id={lic['id']}")

            # 2. Fetch detail (contains full dades with documents inside)
            detail_url = f"{BASE_URL}/detall-publicacio-expedient/{lic['expedientId']}/{lic['id']}"
            log.info(f"[2] GET {detail_url}")
            detail_r = client.get(detail_url)
            log.info(f"    Status: {detail_r.status_code}")
            if detail_r.status_code != 200:
                log.warning(f"    SKIP: status {detail_r.status_code}")
                continue
            detail = detail_r.json()
            log.debug(f"    Detail top-level keys: {list(detail.keys())}")

            # 3. Documents are inside detail['dades']['publicacio']['dadesPublicacio']
            dades = detail.get("dades", {})
            log.debug(
                f"    dades top-level keys: {list(dades.keys()) if dades else 'VACIO'}")
            dades_pub = dades.get("publicacio", {}).get("dadesPublicacio", {})
            log.info(
                f"[3] dadesPublicacio keys: {list(dades_pub.keys()) if dades_pub else 'VACIO'}")
            docs = extract_documents(dades_pub)
            log.info(f"    Documentos encontrados: {len(docs)}")
            for d in docs:
                log.debug(
                    f"      - id={d.get('id')} titol={d.get('titol', '')[:50]}")

            # 4. Download each document
            log.info(f"[4] Descargando {len(docs)} documentos...")
            downloaded = []
            for doc in docs:
                doc_url = f"{BASE_URL}/descarrega-document/{doc['id']}/{doc['hash']}"
                log.info(
                    f"    GET doc id={doc['id']} titol={doc.get('titol', '')[:40]}")
                doc_r = client.get(doc_url)
                log.info(
                    f"    Status: {doc_r.status_code} | Size: {len(doc_r.content)} bytes")
                if doc_r.status_code == 200:
                    safe_name = doc["titol"].replace("/", "_")
                    filepath = DOWNLOAD_DIR / safe_name
                    filepath.write_bytes(doc_r.content)
                    log.info(f"    Guardado en: {filepath}")
                    downloaded.append({
                        "titol": doc["titol"],
                        "mida_kb": round(doc.get("mida", 0) / 1024, 1),
                        "fitxer": str(filepath),
                    })
                else:
                    log.warning(
                        f"    FAIL descarga doc: status {doc_r.status_code}")

            log.info(
                f"    Documentos descargados OK: {len(downloaded)}/{len(docs)}")

            fase = (detail.get("navegacioFases") or [{}])[-1]
            enriched.append({
                "titol": lic["titol"],
                "organ": lic["organ"],
                "pressupost": lic.get("pressupostLicitacio"),
                "expedient": lic.get("codiExpedient"),
                "fase": dades.get("publicacio", {}).get("fase", {}).get("text"),
                "data_publicacio": fase.get("dataPublicacio"),
                "documents": downloaded,
            })

    log.info(f"\n=== TOTAL licitacions enriquidas: {len(enriched)} ===")

    # 5. Ask the model to format and describe everything
    log.info("[5] Enviando datos al modelo...")
    result = await agent(
        prompt=f"Formatea y describe estas licitaciones y sus documentos descargados:\n\n"
        f"{json.dumps(enriched, ensure_ascii=False, indent=2)}"
    ).collect()

    for content in result.output.content:
        print(content.text)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
