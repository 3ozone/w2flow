"""
Descarga licitaciones públicas catalanas — arquitectura SOLID.

Clases:
  TenderConfig              — configuración (datos puros, sin lógica)
  ITenderApiClient          — interfaz de acceso a la API
  ContractacioPublicaClient — implementación concreta de ITenderApiClient
  IDocumentExtractor        — interfaz de extracción de documentos
  DFSDocumentExtractor      — extracción recursiva (DFS) de documentos
  IDocumentDownloader       — interfaz de descarga y persistencia
  LocalDocumentDownloader   — guarda ficheros en disco local
  ITenderEnricher           — interfaz de enriquiment d'una licitació
  TenderEnricher            — fetch detail + extract + download en paral·lel
  IScorer                   — interfaz de puntuació de licitacions
  PDFScorer                 — llegeix PDFs amb pymupdf i calcula puntuació
  IPromptBuilder            — interfaz de construcció del prompt
  LicitacioPromptBuilder    — prompt JSON + PDFs com a File objects
  IAgentRunner              — interfaz per cridar l'agent LLM
  TimbalAgentRunner         — implementació amb timbal Agent
  TenderOrchestrator        — cerca → enriquiment paral·lel
  TenderAnalysisPipeline    — enriquiment → scoring → prompt → agent

Principis aplicats:
  S — cada classe té una única responsabilitat
  O — s'estén afegint noves classes, sense modificar les existents
  L — les implementacions concretes són substituïbles per les seves interfaces
  I — interfaces petites i enfocades (una capacitat cada una)
  D — les classes d'alt nivell depenen d'abstraccions, no d'implementacions
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import pymupdf
from timbal import Agent
from timbal.types.file import File

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants de domini  (S — separades de la lògica)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Configuració (S — datos separados de la lógica)
# ---------------------------------------------------------------------------

@dataclass
class TenderConfig:
    """Paràmetres de configuració del pipeline."""

    base_url: str = "https://contractaciopublica.cat/portal-api"
    download_dir: Path = field(default_factory=lambda: Path("downloads"))
    max_licitacions: int = 10
    http_timeout: int = 30
    search_params: dict = field(default_factory=lambda: {
        "page": 0,
        "size": 20,
        "tipusExpedient": 1,           # solo licitaciones/contratos
        "faseVigent": 0,               # solo en plazo (anunci de licitació)
        "inclourePublicacionsPlacsp": "false",
        "sortField": "dataUltimaPublicacio",
        "sortOrder": "desc",
    })


# ---------------------------------------------------------------------------
# Interfaz I: acceso a la API  (I — interfaz enfocada en lectura de datos)
# ---------------------------------------------------------------------------

class ITenderApiClient(ABC):
    """Contrato para cualquier cliente que acceda a datos de licitaciones."""

    @abstractmethod
    async def fetch_list(self) -> list[dict]:
        """Retorna la llista de licitacions."""

    @abstractmethod
    async def fetch_detail(
        self,
        client: httpx.AsyncClient,
        exp_id: str,
        pub_id: int,
    ) -> dict | None:
        """Retorna el detall complet d'una licitació, o None si falla.""""


# ---------------------------------------------------------------------------
# Interfaz II: extracció de documents  (I — interfaz enfocada en parsing)
# ---------------------------------------------------------------------------

class IDocumentExtractor(ABC):
    """Contrato para extraer documentos de la respuesta de la API."""

    @abstractmethod
    def extract(self, dades: dict) -> list[dict]:
        """Retorna la llista de documents descargables continguts en dades."""


# ---------------------------------------------------------------------------
# Interfaz III: descàrrega i persistència  (I — interfaz enfocada en I/O)
# ---------------------------------------------------------------------------

class IDocumentDownloader(ABC):
    """Contrato para descargar y persistir un documento."""

    @abstractmethod
    async def download(
        self,
        client: httpx.AsyncClient,
        doc: dict,
        lic: dict,
        detail: dict,
    ) -> dict:
        """Descarga el document i retorna els metadades del resultat."""


# ---------------------------------------------------------------------------
# Interfaz IV: enriquiment d'una licitació  (I — interfaz enfocada en enriquiment)
# ---------------------------------------------------------------------------

class ITenderEnricher(ABC):
    """Contrato para enriquecer una licitació: fetch detail + extraer docs + descargar."""

    @abstractmethod
    async def enrich(
        self,
        client: httpx.AsyncClient,
        lic: dict,
    ) -> dict | None:
        """
        Retorna la licitació enriquida amb documents i file_paths,
        o None si no s'ha pogut obtenir el detall.
        """


# ---------------------------------------------------------------------------
# Interfaz V: puntuació  (I — interfaz enfocada en scoring)
# ---------------------------------------------------------------------------

class IScorer(ABC):
    """Contrato para puntuar una lista de licitaciones enriquidas."""

    @abstractmethod
    def score(self, enriched: list[dict]) -> list[dict]:
        """
        Afegeix el camp 'score' a cada licitació i retorna la llista modificada.
        """


# ---------------------------------------------------------------------------
# Interfaz VI: construcció del prompt  (I — interfaz enfocada en prompt)
# ---------------------------------------------------------------------------

class IPromptBuilder(ABC):
    """Contrato para construir el prompt que se enviará al agente LLM."""

    @abstractmethod
    def build(self, enriched: list[dict]) -> list:
        """Retorna la llista de parts del prompt (text + File objects)."""


# ---------------------------------------------------------------------------
# Interfaz VII: execució de l'agent  (I — interfaz enfocada en LLM)
# ---------------------------------------------------------------------------

class IAgentRunner(ABC):
    """Contrato para invocar un agente LLM con un prompt."""

    @abstractmethod
    async def run(self, prompt_parts: list) -> str | None:
        """Envia el prompt a l'agent i retorna el text de resposta, o None si falla."""


# ---------------------------------------------------------------------------
# Implementació concreta I: client de l'API  (S, O, L, D)
# ---------------------------------------------------------------------------

class ContractacioPublicaClient(ITenderApiClient):
    """Accede a contractaciopublica.cat/portal-api."""

    def __init__(self, config: TenderConfig) -> None:
        self._config = config
        self._headers = {"Accept": "application/json, */*"}

    async def fetch_list(self) -> list[dict]:
        """Obté la llista de licitacions més recents segons els paràmetres de configuració."""
        async with httpx.AsyncClient(
            timeout=self._config.http_timeout,
            headers=self._headers,
        ) as client:
            r = await client.get(
                f"{self._config.base_url}/cerca-avancada",
                params=self._config.search_params,
            )
            r.raise_for_status()
            content = r.json().get("content", [])
            licitacions = content[: self._config.max_licitacions]
            log.info("[API] Licitacions obtingudes: %s", len(licitacions))
            return licitacions

    async def fetch_detail(
        self,
        client: httpx.AsyncClient,
        exp_id: str,
        pub_id: int,
    ) -> dict | None:
        """Obté el detall complet d'una licitació i retorna el JSON, o None si falla."""
        url = f"{self._config.base_url}/detall-publicacio-expedient/{exp_id}/{pub_id}"
        r = await client.get(url)
        if r.status_code != 200:
            log.warning("[API] SKIP detall %s/%s — HTTP %s",
                        exp_id, pub_id, r.status_code)
            return None
        return r.json()

    async def fetch_document_bytes(
        self,
        client: httpx.AsyncClient,
        doc_id: int,
        doc_hash: str,
    ) -> bytes | None:
        """Intenta descargar un document i retorna els bytes, o None si falla."""
        url = f"{self._config.base_url}/descarrega-document/{doc_id}/{doc_hash}"
        r = await client.get(url)
        if r.status_code != 200:
            log.warning("[API] SKIP document %s — HTTP %s",
                        doc_id, r.status_code)
            return None
        return r.content


# ---------------------------------------------------------------------------
# Implementació concreta II: extracció DFS  (S, O, L)
# ---------------------------------------------------------------------------

class DFSDocumentExtractor(IDocumentExtractor):
    """Cerca documents descargables en qualsevol nivell del JSON (DFS)."""

    def extract(self, dades: dict) -> list[dict]:
        """Retorna una llista de documents trobats fent una cerca recursiva (DFS) sobre dades."""
        docs: list[dict] = []
        pending: list = [dades]
        while pending:
            node = pending.pop()
            if isinstance(node, dict):
                if (
                    "titol" in node
                    and "hash" in node
                    and isinstance(node.get("id"), int)
                ):
                    docs.append(node)
                else:
                    pending.extend(node.values())
            elif isinstance(node, list):
                pending.extend(node)
        return docs


# ---------------------------------------------------------------------------
# Implementació concreta III: descàrrega a disc local  (S, O, L, D)
# ---------------------------------------------------------------------------

class LocalDocumentDownloader(IDocumentDownloader):
    """Descarga documents i els desa al sistema de fitxers local."""

    def __init__(self, config: TenderConfig, api_client: ContractacioPublicaClient) -> None:
        self._config = config
        self._api = api_client

    async def download(
        self,
        client: httpx.AsyncClient,
        doc: dict,
        lic: dict,
        detail: dict,
    ) -> dict:
        lic_dir = self._config.download_dir / str(lic["expedientId"])
        lic_dir.mkdir(parents=True, exist_ok=True)

        content = await self._api.fetch_document_bytes(client, doc["id"], doc["hash"])

        file_path: str | None = None
        if content is not None:
            safe_name = doc["titol"].replace("/", "_")
            filepath = lic_dir / safe_name
            filepath.write_bytes(content)
            file_path = str(filepath)
            log.info("[DL] ✓ %s (%s bytes)", doc["titol"][:50], len(content))
        else:
            log.warning("[DL] ✗ %s — no es va poder descarregar",
                        doc["titol"][:50])

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


# ---------------------------------------------------------------------------
# Implementació concreta IV: enriquiment complet d'una licitació  (S, O, L, D)
# ---------------------------------------------------------------------------

class TenderEnricher(ITenderEnricher):
    """
    Combina fetch_detail + extract + download per a una sola licitació.

    Equivalent a _fetch_and_download_one() de timbal_workflow.py,
    però desacoblat: rep les dependències per injecció (D).
    """

    def __init__(
        self,
        api_client: ITenderApiClient,
        extractor: IDocumentExtractor,
        downloader: IDocumentDownloader,
    ) -> None:
        self._api = api_client
        self._extractor = extractor
        self._downloader = downloader

    async def enrich(
        self,
        client: httpx.AsyncClient,
        lic: dict,
    ) -> dict | None:
        """Obté el detall d'una licitació, enriqueix amb documents i els descarrega."""
        detail = await self._api.fetch_detail(client, lic["expedientId"], lic["id"])
        if detail is None:
            return None

        docs = self._extractor.extract(detail.get("dades", {}))
        log.info("[ENRICH] %s → %s documents", lic["id"], len(docs))

        # Descarrega tots els documents de la licitació en paral·lel
        download_results = await asyncio.gather(
            *[self._downloader.download(client, doc, lic, detail) for doc in docs]
        )

        file_paths = [
            r["file_path"] for r in download_results if r.get("file_path")
        ]

        fase = (detail.get("navegacioFases") or [{}])[-1]
        dades = detail.get("dades", {})

        return {
            "titol": lic["titol"],
            "organ": lic["organ"],
            "pressupost": lic.get("pressupostLicitacio"),
            "expedient": lic.get("codiExpedient"),
            "fase": dades.get("publicacio", {}).get("fase", {}).get("text"),
            "data_publicacio": fase.get("dataPublicacio"),
            "documents": [
                {"titol": r["document"], "mida_kb": r["mida_kb"]}
                for r in download_results
            ],
            "file_paths": file_paths,
        }


# ---------------------------------------------------------------------------
# Implementació concreta V: puntuació per PDF  (S, O, L)
# ---------------------------------------------------------------------------

class PDFScorer(IScorer):
    """
    Puntua cada licitació llegint el text dels seus PDFs amb pymupdf.

    Criteris (màx 70 pts):
      - Pressupost         0-25 pts  (>1M=25, >500K=20, >100K=10, resta=5)
      - Sector positiu     0-30 pts  (+5 per paraula clau, màx 30)
      - Sector negatiu       0 pts   (-10 per paraula clau IT/software)
      - Procediment obert   10 pts
      - Subcontractació      5 pts
    """

    def score(self, enriched: list[dict]) -> list[dict]:
        log.info("[SCORE] Puntuant %s licitacions...", len(enriched))
        for lic in enriched:
            lic["score"] = self._score_one(lic)
        return enriched

    def _score_one(self, lic: dict) -> dict:
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

        pressupost = lic.get("pressupost") or 0
        if pressupost >= 1_000_000:
            pts_pressupost = 25
        elif pressupost >= 500_000:
            pts_pressupost = 20
        elif pressupost >= 100_000:
            pts_pressupost = 10
        else:
            pts_pressupost = 5

        hits_pos = [kw for kw in SCORE_CONFIG["sector_positiu"] if kw in text]
        pts_sector_pos = min(len(hits_pos) * 5, 30)

        hits_neg = [kw for kw in SCORE_CONFIG["sector_negatiu"] if kw in text]
        pts_sector_neg = len(hits_neg) * -10

        pts_procediment = 10 if "procediment obert" in text else 0
        pts_subcontract = 5 if "subcontract" in text else 0

        total = max(
            0,
            pts_pressupost + pts_sector_pos + pts_sector_neg
            + pts_procediment + pts_subcontract,
        )
        recomanacio = (
            "✅ RECOMANADA" if total >= 50
            else ("⚠️ A VALORAR" if total >= 25 else "❌ NO RECOMANADA")
        )
        log.info(
            "[SCORE] [%s] %s/70 — %s",
            lic.get("expedient", "?"), total, recomanacio,
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


# ---------------------------------------------------------------------------
# Implementació concreta VI: construcció del prompt  (S, O, L, D)
# ---------------------------------------------------------------------------

class LicitacioPromptBuilder(IPromptBuilder):
    """Construeix el prompt amb el JSON de les licitacions i els PDFs com a File objects."""

    def build(self, enriched: list[dict]) -> list:
        all_file_paths = [
            fp for lic in enriched for fp in lic.get("file_paths", [])
        ]
        lic_summary = [
            {k: v for k, v in lic.items() if k != "file_paths"}
            for lic in enriched
        ]
        pdf_files = [
            File.validate(p)
            for p in all_file_paths
            if Path(p).exists() and p.endswith(".pdf")
        ]
        log.info("[PROMPT] PDFs adjunts: %s", len(pdf_files))
        return [
            f"Analiza estas {len(enriched)} licitaciones para nuestra empresa de "
            f"ingeniería/construcción. Tienes adjuntos {len(pdf_files)} documentos "
            "PDF reales para leer. Usa la puntuación precalculada (campo 'score') "
            "y los documentos para justificar la recomendación:\n\n"
            + json.dumps(lic_summary, ensure_ascii=False, indent=2),
            *pdf_files,
        ]


# ---------------------------------------------------------------------------
# Implementació concreta VII: agent timbal  (S, O, L, D)
# ---------------------------------------------------------------------------

class TimbalAgentRunner(IAgentRunner):
    """Crida un Agent de timbal i retorna el text de la resposta."""

    def __init__(self, model: str = "google/gemini-2.5-flash") -> None:
        self._agent = Agent(
            name="LicitacionsAgent",
            model=model,
            system_prompt=SYSTEM_PROMPT,
        )

    async def run(self, prompt_parts: list) -> str | None:
        log.info("[AGENT] Cridant l'agent...")
        result = await self._agent(prompt=prompt_parts).collect()
        if result.output is None:
            log.error("[AGENT] Sense resposta. Comprova la GEMINI_API_KEY.")
            return None
        return result.output.collect_text()


# ---------------------------------------------------------------------------
# Orquestrador  (D — depèn d'abstraccions, no d'implementacions)
# ---------------------------------------------------------------------------

class TenderOrchestrator:
    """Coordina el flux complet: cerca → enriquiment paral·lel."""

    def __init__(
        self,
        api_client: ITenderApiClient,
        enricher: ITenderEnricher,
        config: TenderConfig,
    ) -> None:
        self._api = api_client
        self._enricher = enricher
        self._config = config

    async def run(self) -> list[dict]:
        """Executa el pipeline complet i retorna les licitacions enriquides."""
        licitacions = await self._api.fetch_list()
        self._config.download_dir.mkdir(exist_ok=True)
        log.info("[ORCH] Enriquint %s licitacions en paral·lel...",
                 len(licitacions))

        async with httpx.AsyncClient(
            timeout=self._config.http_timeout,
            headers={"Accept": "application/json, */*"},
        ) as client:
            raw_results = await asyncio.gather(
                *[self._enricher.enrich(client, lic) for lic in licitacions]
            )

        enriched = [r for r in raw_results if r is not None]
        total_pdfs = sum(len(r.get("file_paths", [])) for r in enriched)
        log.info("[ORCH] Licitacions enriquides: %s | PDFs: %s",
                 len(enriched), total_pdfs)
        return enriched


# ---------------------------------------------------------------------------
# Pipeline d'anàlisi complet  (O — estén sense modificar TenderOrchestrator)
# ---------------------------------------------------------------------------

class TenderAnalysisPipeline:
    """
    Afegeix scoring + prompt building + agent al TenderOrchestrator.

    Principi O: TenderOrchestrator queda intacte;
    aquest pipeline el compon amb les noves capacitats.
    Principi D: rep les abstraccions per injecció, no instancia res.
    """

    def __init__(
        self,
        orchestrator: TenderOrchestrator,
        scorer: IScorer,
        prompt_builder: IPromptBuilder,
        agent_runner: IAgentRunner,
    ) -> None:
        self._orchestrator = orchestrator
        self._scorer = scorer
        self._prompt_builder = prompt_builder
        self._agent_runner = agent_runner

    async def run(self) -> str | None:
        """Executa el pipeline complet i retorna la resposta de l'agent."""
        # Pas 1+2: cerca i enriquiment (fetch + download)
        enriched = await self._orchestrator.run()

        # Pas 3: puntuació
        enriched = self._scorer.score(enriched)

        # Pas 4: construcció del prompt
        prompt_parts = self._prompt_builder.build(enriched)

        # Pas 5: agent LLM
        return await self._agent_runner.run(prompt_parts)


# ---------------------------------------------------------------------------
# Composició i punt d'entrada  (D — el main construeix les dependències)
# ---------------------------------------------------------------------------

def build_orchestrator(config: TenderConfig | None = None) -> TenderOrchestrator:
    """Construeix l'orquestrador bàsic (cerca + enriquiment)."""
    cfg = config or TenderConfig()
    api_client = ContractacioPublicaClient(cfg)
    extractor = DFSDocumentExtractor()
    downloader = LocalDocumentDownloader(cfg, api_client)
    enricher = TenderEnricher(api_client, extractor, downloader)
    return TenderOrchestrator(api_client, enricher, cfg)


def build_analysis_pipeline(
    config: TenderConfig | None = None,
    model: str = "google/gemini-2.5-flash",
) -> TenderAnalysisPipeline:
    """Construeix el pipeline complet: cerca + enriquiment + scoring + agent."""
    orchestrator = build_orchestrator(config)
    return TenderAnalysisPipeline(
        orchestrator=orchestrator,
        scorer=PDFScorer(),
        prompt_builder=LicitacioPromptBuilder(),
        agent_runner=TimbalAgentRunner(model=model),
    )


async def main() -> None:
    """Punt d'entrada: construeix i executa el pipeline complet."""
    log.info("=== INICIO PIPELINE ===")
    pipeline = build_analysis_pipeline()
    output = await pipeline.run()
    if output:
        print(output)


if __name__ == "__main__":
    asyncio.run(main())
