# PENDING — Tareas pendientes w2flow

---

## Fase A — Reescribir dominio desde cero (solo entidades y value objects, con docstrings)

### Value objects

- [x] `TEST` + `IMPL` `TrafficLight` — enum GREEN/YELLOW/RED con `from_score()` (umbrales 70/40) ✅
- [x] `TEST` + `IMPL` `Score` — frozen dataclass con `total`, `is_viable()`, `assign_traffic_light()` ✅
- [x] `TEST` + `IMPL` `DocumentType` ✅
  - Enum: `PCAP`, `PPT`, `TECHNICAL_MEMORY`, `BUDGET`, `ANNEXES`, `UNKNOWN`
  - `from_api_section(section_key: str)` — mapea clave JSON de la API al tipo (no `from_title`)
  - Claves confirmadas empíricamente: `plecsDeClausulesAdministratives` → PCAP, `plecsDePrescripcionsTecniques` → PPT, `memoriaJustificativaContracte` → TECHNICAL_MEMORY
  - `BUDGET` y `ANNEXES` no tienen sección propia confirmada — pendiente de revisar con más licitaciones

### Entidades

- [x] `TEST` + `IMPL` `Tender` — campos RF-02 + filtros RF-03/RN-09/RN-10 (ver diseño abajo) ✅
- [x] `TEST` + `IMPL` `Document` — dataclass con `doc_type: DocumentType`, `doc_id: int`, `titol: str`, `hash: str`, `mida: int` ✅
- [x] `TEST` + `IMPL` `ScoredTender` — agrupa `Tender` + `Score`, método `is_viable()` ✅
- [x] `TEST` + `IMPL` `ComparativeReport` — lista de `ScoredTender`, método `get_viable_tenders()` ✅
- [x] `TEST` + `IMPL` `DocumentAnalysis` — resultat de l'anàlisi NLP d'un document (RF-05, RN-12) ✅

### FilterConfig

- [x] `TEST` + `IMPL` `FilterConfig` ✅
  - Filtros nativos API (van en `to_api_params()`): `tipus_expedient`, `fase_vigent`, `ambit`, `tipus_contracte`, `procediment_adjudicacio`
  - Filtros post-fetch (van en `matches()`): `cpv_codes`, `pressupost_maxim`, `nuts_codes`, `classifications`, `durada_minima_dies`, `durada_maxima_dies`
  - Reglas: RN-07 (CPV), RN-08 (presupuesto), RN-09 (NUTS), RN-10 (clasificación), RN-11 (duración)

---

## Diseño de Tender (confirmado 08/05/2026)

Campos obligatorios RF-02:

| Campo | Tipo | Fuente API |
|---|---|---|
| `expedient_id` | `str` | listado: `expedientId` (UUID, identificador único) |
| `publicacio_id` | `int` | listado: `id` |
| `codi_expedient` | `str \| None` | detalle: `dadesBasiquesPublicacio.codiExpedient` (nullable) |
| `organ` | `str` | listado: `organ` |
| `titol` | `str` | listado: `titol` |
| `pressupost` | `float \| None` | detalle: `dadesPublicacio.pressupostLicitacio` |
| `cpv_principal` | `str \| None` | detalle: `dadesPublicacioLot[0].cpvPrincipal.codi` |
| `data_limit` | `datetime \| None` | detalle: `dadesPublicacio.dataTerminiPresentacioOSolicitud` |
| `durada_dies` | `int \| None` | detalle: `dadesPublicacioLot[0].duradaTermini` (calculado) |

Campos para filtros RF-03/RN-09/RN-10:

| Campo | Tipo | Fuente API |
|---|---|---|
| `tipus_contracte_id` | `int \| None` | detalle: `dadesBasiquesPublicacio.tipusContracte.id` |
| `procediment_id` | `int \| None` | detalle: `dadesBasiquesPublicacio.procedimentAdjudicacio.id` |
| `nuts_code` | `str \| None` | detalle: `dadesPublicacioLot[0].llocExecucio.codiNuts` |
| `classifications` | `tuple[str, ...]` | detalle: `dadesPublicacioLot[0].classificacionsEmpresarials[].grupClassificacioEmpresarial` |

Métodos de negocio:

| Método | Regla |
|---|---|
| `is_expired(today: date) -> bool` | RN-05 — `data_limit.date() < today` |

---

## Fase A.1 — Capa de aplicación (ports, use cases, DTOs)

### Ports — contratos ABC que la infraestructura implementarà

- [x] `IMPL` `TenderApiPort` ✅
- [x] `IMPL` `TenderRepositoryPort` ✅
- [x] `IMPL` `NlpAnalyserPort` ✅
- [x] `IMPL` `FilterRepositoryPort` ✅

### Use Cases — orquestació del domini

- [x] `TEST` + `IMPL` `FetchCandidatesUseCase` — cerca + filtra + descarta expirades (RF-02, RF-03, RN-01, RN-05) ✅
  - Passa `FilterConfig` com a paràmetre
  - Crida `TenderApiPort.fetch_tenders()` amb `config.to_api_params()`
  - Aplica `config.matches(tender)` i `tender.is_expired()` en memòria
  - Descarta duplicats via `TenderRepositoryPort.is_duplicate()`
  - Retorna `list[Tender]`
- [x] `TEST` + `IMPL` `RunPipelineUseCase` — orquestra tot el pipeline (RF-04, RF-05, RF-06, RF-07) ✅
  - **Fix**: afegit `TenderRepositoryPort` al constructor i `repository.save()` per a cada tender processat ✅
  - Rep `FilterConfig` com a paràmetre
  - Crida `FetchCandidatesUseCase` per obtenir candidats
  - Per cada `Tender`, obté documents via `TenderApiPort.fetch_documents()` i descarrega els obligatoris
  - Analitza amb `NlpAnalyserPort.analyse()` → `DocumentAnalysis`
  - Genera `Score` via `analysis.to_score()`
  - Retorna `ReportDTO` amb `ScoredTenderDTO` per cada licitació

### DTOs — transferència de dades cap a presentació

- [x] `IMPL` `ScoredTenderDTO` — dades aplanades per al panell (titol, organ, pressupost, total, semàfor) ✅
- [x] `IMPL` `ReportDTO` — tupla de `ScoredTenderDTO` + resum (total candidats, total viables) ✅

---

## Fase B — Infraestructura (desde cero)

### Configuració de base de dades

- [x] `IMPL` `database.py` — engine SQLAlchemy + SessionLocal + Base declarativa ✅

### Models ORM (SQLAlchemy)

- [x] `IMPL` `TenderModel` — taula `tenders` amb tots els camps de `Tender` ✅
  - `expedient_id` (PK, UUID), `publicacio_id`, `organ`, `titol`
  - `codi_expedient`, `pressupost`, `cpv_principal`, `data_limit`, `durada_dies`
  - `tipus_contracte_id`, `procediment_id`, `nuts_code`, `classifications` (ARRAY)
- [x] `IMPL` `FilterConfigModel` — taula `filter_configs` amb tots els camps de `FilterConfig` ✅
  - `id` (PK, autoincrement), `is_active` (bool), `created_at` (timestamp)
  - Filtres natius: `tipus_expedient`, `fase_vigent`, `ambit`, `tipus_contracte`, `procediment_adjudicacio`
  - Filtres post-fetch: `cpv_codes` (ARRAY), `pressupost_maxim`, `nuts_codes` (ARRAY), `classifications` (ARRAY), `durada_minima_dies`, `durada_maxima_dies`

### Migració Alembic

- [x] Migració inicial — crear taules `tenders` i `filter_configs` des de zero ✅

### Repositoris (implementen ports d'aplicació)

> Tests d'integració amb SQLite en memòria (no unitaris)

- [x] `TEST (integració)` + `IMPL` `SqlAlchemyTenderRepository` — implementa `TenderRepositoryPort` ✅
  - `is_duplicate(expedient_id) -> bool` — SELECT EXISTS
  - `save(tender: Tender) -> None` — INSERT via ORM
- [x] `TEST (integració)` + `IMPL` `SqlAlchemyFilterRepository` — implementa `FilterRepositoryPort` ✅
  - `save(config: FilterConfig) -> None` — INSERT + desactivar anteriors
  - `get_active() -> FilterConfig` — SELECT WHERE is_active=True
  - `list_all() -> list[FilterConfig]` — SELECT ALL

### Serveis externs (implementen ports d'aplicació)

- [x] `TEST (unitari, mock HTTP)` + `IMPL` `ContractacioPublicaClient` — implementa `TenderApiPort` ✅
  - `fetch_tenders(params: dict) -> list[Tender]` — GET /cerca-avancada (paginat)
  - `fetch_documents(expedient_id, publicacio_id) -> list[Document]` — GET /detall-publicacio-expedient + extracció per secció
  - `download_document(doc_id, hash) -> bytes` — GET /descarrega-document
- [x] `IMPL` `TimbalNlpAnalyser` — implementa `NlpAnalyserPort` (sense test — servei extern complex) ✅
  - `analyse(expedient_id, documents) -> DocumentAnalysis` — agent Timbal (RF-05)

### Composició i injecció de dependències

- [x] `IMPL` `dependencies.py` — Composition Root FastAPI ✅
  - `get_db()` — proveïdor de sessió SQLAlchemy
  - `get_fetch_candidates_use_case()` — ensambla `FetchCandidatesUseCase`
  - `get_run_pipeline_use_case()` — ensambla `RunPipelineUseCase`

### Excepcions per capes

- [x] `TEST` + `IMPL` `InvalidScoreError` (`domain/exceptions/`) — puntuació fora de rang (0-100) ✅
  - Es llança a `DocumentAnalysis.__post_init__` si algun criteri és negatiu o supera el màxim
- [x] `IMPL` `NoActiveFilterConfigError` (`application/exceptions/`) ✅
- [x] `IMPL` `TenderApiError` (`application/exceptions/`) ✅
- [x] `IMPL` `exception_handlers.py` (infra/api) — conversió d'excepcions a respostes HTTP ✅
  - `NoActiveFilterConfigError` → 404
  - `TenderApiError` → 502
  - `Exception` → 500

### API (routers + templates)

- [x] `IMPL` `pipeline_router.py` — `POST /api/v1/pipeline/run` → crida `RunPipelineUseCase` ✅
- [x] `IMPL` `tenders_router.py` — `GET /api/v1/tenders` → llista licitacions de la BD ✅
- [x] `IMPL` `filters_router.py` — `GET /api/v1/filters` + `GET /api/v1/filters/active` + `POST /api/v1/filters` ✅
- [ ] `IMPL` templates Jinja2 — panell HTML amb resultats i semàfor
- [x] `IMPL` `main.py` — reescrit amb routers i exception handlers ✅

---

## Fase C — Millores post-integració

### Afegir `max_licitacions` a `FilterConfig` (RN-13)

Permet a l'usuari configurar quantes licitacions vol processar per execució del pipeline.

- [x] `TEST` + `IMPL` `FilterConfig` — afegir camp `max_licitacions: int = 20` i usar-lo com a `size` a `to_api_params()` ✅
- [x] `IMPL` `FilterConfigModel` — afegir columna `max_licitacions INTEGER NOT NULL DEFAULT 20` ✅
- [x] `IMPL` migració Alembic — `ALTER TABLE filter_configs ADD COLUMN max_licitacions` ✅
- [x] `TEST` + `IMPL` `SqlAlchemyFilterRepository` — persistir i restaurar `max_licitacions` ✅
- [x] `IMPL` `FilterConfigRequest` — afegir camp `max_licitacions: int = 20` al schema Pydantic ✅
- [x] `IMPL` `openapi.yaml` — documentar el nou camp ✅

---

## Fase D — Persistència de documents descarregats

Permet que els PDFs descarregats durant el pipeline es guardin a disc i es puguin servir via API.

**Context**: `ContractacioPublicaClient.download_document()` ja descarrega els bytes, però el pipeline els descarta en memòria després del NLP. L'app antiga guardava els fitxers a `downloads/{expedient_id}/`.

- [ ] `TEST` + `IMPL` port `DocumentStoragePort` — `save(expedient_id, filename, content: bytes) -> Path` i `list_documents(expedient_id) -> list[str]`
- [ ] `TEST` + `IMPL` `LocalFileDocumentStorage` — implementació que escriu a `downloads/{expedient_id}/`
- [ ] `IMPL` `run_pipeline_use_case.py` — guardar els bytes descarregats via `DocumentStoragePort` en lloc de descartar-los
- [ ] `TEST` + `IMPL` endpoint `GET /api/v1/tenders/{expedient_id}/documents` — llista els fitxers guardats
- [ ] `TEST` + `IMPL` endpoint `GET /api/v1/tenders/{expedient_id}/documents/{filename}` — retorna el fitxer com a `FileResponse`
- [ ] `IMPL` `openapi.yaml` — documentar els nous endpoints
- [ ] `IMPL` `dependencies.py` — afegir `get_document_storage() -> DocumentStoragePort`

---

## Fase E — Correcció dels paràmetres de cerca a l'API (fix crític de scoring)

**Context**: Descobert el 09/05/2026 que:
1. `faseVigent=0` retorna barreja d'`ALERTA_FUTURA` (sense documents) i `ANUNCI_LICITACIO` → scoring = 0
2. El valor correcte per filtrar "Anunci de licitació" és `faseVigent=1000040` (confirmat via Dades Mestres)
3. Sense `ambit=1500001` la resposta és quasi tot `ALERTA_FUTURA`
4. `tipusContracte=395` (Obres) i `procedimentAdjudicacio=401` (Obert) maximitzen la rellevància

**Objectiu**: Fer que `FilterConfig.to_api_params()` generi els paràmetres correctes per defecte i que el `ContractacioPublicaClient` descarti `ALERTA_FUTURA` com a salvaguarda addicional.

### E.1 — Corregir valors per defecte de `FilterConfig`

- [x] `TEST` — actualitzar tests de `FilterConfig.to_api_params()` per validar `fase_vigent=1000040`, `ambit=1500001`, `tipus_contracte=395` ✅
- [x] `IMPL` `FilterConfig` — canviar valors per defecte: `fase_vigent=1000040`, `ambit=1500001`, `tipus_contracte=395`, `procediment_adjudicacio=401` ✅
- [x] `IMPL` migració Alembic — actualitzar `server_default` de les columnes afectades a `filter_configs` ✅

### E.2 — Afegir filtre de seguretat `ALERTA_FUTURA` al client API

- [x] `TEST` — afegir test que verifiqui que `fetch_tenders()` descarta ítems on `fasesVigents` **només** té `ALERTA_FUTURA` ✅
- [x] `IMPL` `ContractacioPublicaClient.fetch_tenders()` — post-filtrar ítems que no tinguin `ANUNCI_LICITACIO` a `fasesVigents` ✅
- [x] `IMPL` `ContractacioPublicaClient._parse_tender()` — usar `fasesVigents.ANUNCI_LICITACIO.idPublicacio` com a `publicacio_id` quan existeixi, en lloc del camp `id` arrel ✅

### E.3 — Actualitzar documentació i openapi

- [x] `IMPL` `openapi.yaml` — actualitzar valors per defecte de `FilterConfigRequest` (fase_vigent, ambit, tipus_contracte) ✅
- [x] `IMPL` `docs/requirements/requirements.md` — documentar RN-14 i RN-15 (actualitzat sessió anterior) ✅

---

## Fase F — Correcció del valor `faseVigent` (descoberta 10/05/2026)

**Context**: Els valors del catàleg de Dades Mestres (`1000040`, etc.) **no funcionen** al paràmetre `faseVigent` de `/cerca-avancada`. El portal usa un sistema propi en múltiples de 10. Valors confirmats via inspecció de xarxa:
- `0` = Alerta futura (sense documents) ← incorrecte per a w2flow
- `30` = Anunci de licitació en termini ← **valor correcte**
- `40` = Expedient en avaluació, `50` = Adjudicació...

A més, `sortField=dataUltimaPublicacio&sortOrder=desc` són **obligatoris** (ja implementats a `to_api_params()`).

### F.1 — Corregir `fase_vigent` default a `FilterConfig`

- [x] `TEST` — actualitzar `test_default_fase_vigent` per validar `fase_vigent == 30` ✅
- [x] `TEST` — actualitzar `test_to_api_params_includes_defaults` per validar `faseVigent=30` ✅
- [x] `IMPL` `FilterConfig` — canviar `fase_vigent: int = 1000040` → `fase_vigent: int = 30` ✅
- [x] `IMPL` migració Alembic — actualitzar `server_default` de `fase_vigent`: `'1000040'` → `'30'` ✅

### F.2 — Actualitzar documentació i openapi

- [x] `IMPL` `openapi.yaml` — corregit default de `fase_vigent`: `1000040` → `30` ✅
- [x] `IMPL` `docs/api-contractaciopublica/README.md` — taula `faseVigent` amb valors reals ✅
- [x] `IMPL` `docs/requirements/requirements.md` — RN-14 corregit ✅

---

## Fase G — Desacoplament del model LLM (config-driven, Opció A)

**Context**: El pipeline funciona correctament però `gemini-2.0-flash` falla amb `429 RESOURCE_EXHAUSTED` (quota free tier exhaurida). Es desacobla el model LLM perquè sigui configurable via `.env` sense canviar codi.

**Disseny (Opció A — config-driven)**:
- `config.py` exposa `llm_model: str` i `llm_api_key: str`
- `TimbalNlpAnalyser` detecta el provider del model (`model.split("/")[0]`)
- Providers amb suport natiu de PDF (`google`, `anthropic`) → envien `File` objects
- Resta de providers (`groq`, `openai`, `mistral`...) → extreuen text amb `pymupdf` i envien text pla
- Canviar de model = solo canviar `.env`, zero canvis de codi

```bash
# Groq (gratuït)
LLM_MODEL=groq/llama-3.3-70b-versatile
LLM_API_KEY=gsk_xxx

# Gemini (quota diària free)
LLM_MODEL=google/gemini-2.0-flash
LLM_API_KEY=AIza_xxx

# Anthropic (de pagament, suport PDF natiu)
LLM_MODEL=anthropic/claude-3-5-sonnet-20241022
LLM_API_KEY=sk-ant-xxx
```

**Impacte**: `TimbalNlpAnalyser` + `config.py` + `dependencies.py`. El port `NlpAnalyserPort` no canvia.

### G.1 — Test de `_extract_text_from_pdfs()`

- [ ] `TEST` `TimbalNlpAnalyser._extract_text_from_pdfs()` — donat bytes d'un PDF vàlid retorna text no buit; bytes invàlids retorna string buit; llista buida retorna string buit

### G.2 — Implementació de `_extract_text_from_pdfs()`

- [ ] `IMPL` `TimbalNlpAnalyser._extract_text_from_pdfs(documents: list[bytes]) -> str` — usa `pymupdf` (`fitz`) per extreure text de cada pàgina i concatenar-lo

### G.3 — Refactor de `TimbalNlpAnalyser` per ser config-driven

- [ ] `IMPL` `TimbalNlpAnalyser.__init__(model: str, api_key: str)` — paràmetres genèrics (eliminar `gemini_api_key`)
- [ ] `IMPL` `TimbalNlpAnalyser.analyse()` — detectar provider: si `google` o `anthropic` → `File` objects; sinó → `_extract_text_from_pdfs()`
- [ ] `IMPL` `_PDF_CAPABLE_PROVIDERS = {"google", "anthropic"}` — constant de classe

### G.4 — Actualitzar config i dependencies

- [ ] `IMPL` `config.py` — substituir `gemini_api_key` per `llm_model: str = "google/gemini-2.0-flash"` i `llm_api_key: str = ""`
- [ ] `IMPL` `dependencies.py` — passar `settings.llm_model` i `settings.llm_api_key` a `TimbalNlpAnalyser`
- [ ] `IMPL` `.env` — canviar `GEMINI_API_KEY` per `LLM_MODEL` + `LLM_API_KEY` (no commitejar)
