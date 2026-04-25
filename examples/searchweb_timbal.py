import json
from pathlib import Path

import httpx
from timbal import Agent

BASE_URL = "https://contractaciopublica.cat/portal-api"
DOWNLOAD_DIR = Path("downloads")
MAX_LICITACIONS = 3  # Limit to avoid too many requests

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
        if "titol" in data and "path" in data and isinstance(data.get("id"), int):
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

    with httpx.Client(timeout=30, headers={"User-Agent": "w2flow/1.0"}) as client:
        # 1. Fetch licitacions list
        response = client.get(
            f"{BASE_URL}/cerca-avancada", params=SEARCH_PARAMS)
        response.raise_for_status()
        licitacions = response.json()["content"][:MAX_LICITACIONS]

        enriched = []
        for lic in licitacions:
            # 2. Fetch full detail to get documents
            detail_r = client.get(
                f"{BASE_URL}/detall-publicacio/{lic['expedientId']}/{lic['id']}"
            )
            if detail_r.status_code != 200:
                continue
            detail = detail_r.json()

            # 3. Extract all document objects from detail
            docs = extract_documents(detail.get("dades", {}))

            # 4. Download each document
            downloaded = []
            for doc in docs:
                doc_r = client.get(
                    f"{BASE_URL}/descarrega-document/{doc['id']}/{doc['path']}"
                )
                if doc_r.status_code == 200:
                    safe_name = doc["titol"].replace("/", "_")
                    filepath = DOWNLOAD_DIR / safe_name
                    filepath.write_bytes(doc_r.content)
                    downloaded.append({
                        "titol": doc["titol"],
                        "mida_kb": round(doc.get("mida", 0) / 1024, 1),
                        "fitxer": str(filepath),
                    })

            # Get active phase name
            fase = next(iter(detail.get("navegacioFases", [{}])[-1:]), {})
            enriched.append({
                "titol": lic["titol"],
                "organ": lic["organ"],
                "pressupost": lic.get("pressupostLicitacio"),
                "expedient": lic.get("codiExpedient"),
                "fase": detail.get("dades", {}).get("publicacio", {}).get("fase", {}).get("text"),
                "data_publicacio": fase.get("dataPublicacio"),
                "documents": downloaded,
            })

    # 5. Ask the model to format and describe everything
    result = await agent(
        prompt=f"Formatea y describe estas licitaciones y sus documentos descargados:\n\n"
        f"{json.dumps(enriched, ensure_ascii=False, indent=2)}"
    ).collect()

    for content in result.output.content:
        print(content.text)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
