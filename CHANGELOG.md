# Changelog — w2flow

Totes les versions segueixen [Semantic Versioning](https://semver.org/).

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
