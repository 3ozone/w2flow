# Changelog — w2flow

Totes les versions segueixen [Semantic Versioning](https://semver.org/).

---

## [v2.0.0] - 13-5-2026

### Afegit

#### Fase J — Documents adjunts, comentaris LLM i persistència completa
- Entitat de domini `TenderDocument` — `expedient_id`, `filename`, `filepath`, `comentari_llm`, `created_at`
- `DocumentAnalysis` ampliat amb `comentaris_per_doc: dict[str, str]` i `recomendacio: str`
- Prompt NLP ampliat: el LLM retorna JSON amb comentaris per document i recomanació GO/NO GO
- `NlpAnalyserPort.analyse()` accepta ara `filenames: list[str] | None`
- Port `DocumentStoragePort` + implementació `LocalFileDocumentStorage` (escriu a `downloads/<id>/`)
- Port `TenderDocumentRepositoryPort` + `SqlAlchemyTenderDocumentRepository`
- Model ORM `TenderDocumentModel` — taula `tender_documents` amb FK a `tenders`
- Noves columnes a `TenderModel`: `created_at`, `score_total`, `score_traffic_light`, `score_detall`, `recomendacio`
- Migració Alembic per a les noves taules i columnes
- `RunPipelineUseCase` actualitzat: guarda PDFs a disc, persista documents a BD, crida `update_score()` post-NLP
- `TenderRepositoryPort` + `SqlAlchemyTenderRepository` — nou mètode `update_score()`
- `ScoredTenderDTO` — nous camps `recomendacio: str` i `created_at: datetime | None`
- Endpoint `GET /documents/{expedient_id}/{filename}/download` — serveix PDFs com a `FileResponse`
- Endpoint `DELETE /documents/{expedient_id}/{filename}` — elimina de disc i BD
- Vista `/licitacions` ara llegeix de BD (no de `_last_report`): `TenderModel` + `TenderDocumentModel`
- Layout expandible a `tenders.html`: desglose 5 criteris, llista de documents amb comentari LLM plegable, bloc recomanació GO/NO GO
- Columna `Data` (DD/MM/YYYY) a la taula de licitacions
- Botons ⬇ download i ✕ delete per cada document
- Dashboard (`/`) simplificat: al completar pipeline mostra botó "Veure licitacions →"

#### Fase H — Millores pipeline
- `ScoredTenderDTO` — camp `detall: dict[str, int]` amb desglose dels 5 criteris de RN-12
- `FetchCandidatesUseCase` — paginació automàtica: calcula pàgina inicial des de `count()`, evita reprocessar duplicats
- `TenderRepositoryPort` + `SqlAlchemyTenderRepository` — nou mètode abstracte `count()`

#### Fase G — Desacoblament del model LLM (config-driven)
- `config.py` — substituït `gemini_api_key` per `llm_model: str` i `llm_api_key: str`
- `TimbalNlpAnalyser` — detecta provider del model; providers amb suport PDF natiu (`google`, `anthropic`) envien `File` objects; la resta usen `pymupdf` per extreure text (truncat a 32.000 chars)
- `_PDF_CAPABLE_PROVIDERS = {"google", "anthropic"}` — constant configurable
- `.env` suporta ara qualsevol model LiteLLM: `groq/llama-3.3-70b-versatile`, `google/gemini-2.0-flash`, `anthropic/claude-3-5-sonnet`

#### Fases E–F — Correccions paràmetres API
- `FilterConfig` — valors per defecte corregits: `fase_vigent=30` (Anunci de licitació), `ambit=1500001`, `tipus_contracte=395`, `procediment_adjudicacio=401`
- `ContractacioPublicaClient.fetch_tenders()` — descarta ítems sense `ANUNCI_LICITACIO` a `fasesVigents`
- `ContractacioPublicaClient._parse_tender()` — usa `fasesVigents.ANUNCI_LICITACIO.idPublicacio` com a `publicacio_id`

### Corregit
- `SqlAlchemyTenderRepository.save()` — afegit `session.flush()` per garantir la FK de `tender_documents` (evita `ForeignKeyViolation`)
- `_run_pipeline_task()` a `ui_router.py` — afegit `db.commit()` al final del pipeline i `db.rollback()` al bloc d'error (sense commit la sessió feia rollback en tancar)
- `SqlAlchemyTenderRepository` — `def list_all()` quedava fusionat amb `save()` per un replace incorrecte; restaurat correctament

---

## [1.0.0] — 2026-05-02

Primera versió de producció. Inclou el projecte complet des del domini fins al frontend.

### Afegit

#### Fase 1–3 — Domini, Aplicació i Infraestructura
- Entitats de domini: `Tender`, `Document`, `Score`, `ScoredTender`, `ComparativeReport`
- Value objects: `DocumentType`, `FilterConfig`, `Requirements`, `Score`, `TrafficLight`
- Excepcions de domini i validació en `__post_init__`
- Casos d'ús: `DownloadDocumentsCommand`, `FilterTendersCommand`, `RunPipelineCommand`, `ScoreTendersCommand`
- Repositoris PostgreSQL via SQLAlchemy: `TenderRepository`, `DocumentRepository`
- Migracions Alembic (`create_tables`)
- Client HTTP `ContractacioPublicaClient` per a contractaciopublica.cat
- Servei d'anàlisi narrativa `AnalysisService` (Gemini via Timbal)

#### Fase 4 — API REST
- `GET/PUT /api/v1/filters` — configuració de filtres actius
- `GET /api/v1/tenders` — llistat de licitacions puntuades
- `GET /api/v1/reports`, `GET /api/v1/reports/{id}` — informes comparatius
- `GET /api/v1/reports/{id}/analysis` — anàlisi narrativa
- `POST /api/v1/pipeline/run`, `GET /api/v1/pipeline/status` — execució i estat del pipeline

#### Fase 7 — Millores i correccions
- Logging configurable via `app_debug` (DEBUG/INFO)
- Eliminat filtre UNKNOWN que impedia descarregar la majoria de documents
- `DocumentRepository` escriu bytes a disc i metadata a PostgreSQL (substitueix `LocalDocumentStorage`)

#### Fase 8 — Nous endpoints
- `GET /api/v1/tenders/{id}/documents` — llistat de documents d'una licitació
- `GET /api/v1/tenders/{id}/documents/{doc_id}/download` — descàrrega del PDF
- `DELETE /api/v1/tenders/{id}` — elimina licitació i documents/scores en cascada
- `DELETE /api/v1/reports/{id}` — elimina informe de l'store en memòria
- `GET /api/v1/health` — health check amb estat de la DB

#### Fase 9 — Frontend HTMX + Jinja2
- Layout base (`base.html`) amb navbar, HTMX i TailwindCSS via CDN
- Dashboard (`/`) — filtre actiu, botó "Executar Pipeline", polling d'estat cada 2s
- Pàgina de licitacions (`/tenders`) — taula amb semàfor 🟢🟡🔴, expansió de documents via HTMX
- Pàgina d'informes (`/reports`, `/reports/{id}`) — cards + taula de tenders puntuats + anàlisi Gemini colapsable
- Pàgina de filtres (`/filters`) — formulari complet amb enviament JSON via `fetch`
- Badge de salut DB en temps real (`/partials/health`)

### Canviat
- `pyproject.toml`: afegit `jinja2>=3.1` i `python-multipart>=0.0.9`
- `main.py`: munta `StaticFiles`, configura `Jinja2Templates`, registra `ui_router`
- `TenderRepositoryPort`: nous mètodes abstractes `list_documents` i `delete`

### Corregit
- Hash SRI del CDN HTMX que bloquejava la càrrega
- Firma de `TemplateResponse` actualitzada per a Starlette >= 0.36
- Path incorrecte a `Jinja2Templates` en `ui_router.py`
- Formulari de filtres: substituït `hx-ext="json-enc"` per `fetch` natiu

---

## [Unreleased]

- `Dockerfile` + `.dockerignore`
- Manifests Kubernetes (`deployment.yaml`, `service.yaml`, `configmap.yaml`, `secret.yaml`)
