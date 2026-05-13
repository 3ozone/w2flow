# Arquitectura

## Stack
- **Lenguaje:** Python 3.13
- **API REST:** FastAPI (port 8089)
- **Workflow / Agentes:** Timbal + LiteLLM (config-driven via `.env`)
- **Base de datos:** PostgreSQL + SQLAlchemy ORM + Alembic migrations
- **Frontend:** Jinja2 + HTMX + Tailwind CSS
- **Fuente de datos:** contractaciopublica.cat

---

## Estructura de carpetes

```
app/
├── config.py                         # Settings via pydantic-settings (.env)
├── main.py                           # FastAPI app factory + registre de routers
│
├── domain/                           # Nucli — sense dependències externes
│   ├── entities/
│   │   ├── tender.py                 # Entitat Tender (expedient, organ, pressupost, cpv…)
│   │   ├── document.py               # Entitat Document (docId, hash, midaKb, tipus)
│   │   ├── scored_tender.py          # Agrupació Tender + Score + DocumentAnalysis
│   │   ├── comparative_report.py     # Llista de ScoredTender + totals
│   │   ├── tender_document.py        # Document persistit a disc + comentari LLM (J.2)
│   │   └── document_analysis.py     # Resultat NLP: scores, comentaris_per_doc, recomendacio (J.2)
│   ├── value_objects/
│   │   ├── filter_config.py          # Tots els paràmetres de filtre + to_api_params()
│   │   ├── score.py                  # Puntuació 0–100 + TrafficLight + detall 5 criteris
│   │   ├── traffic_light.py          # Enum: green≥70 / yellow 40–69 / red<40
│   │   └── document_type.py          # Enum: PCAP, PPT, TECHNICAL_MEMORY, BUDGET, ANNEXES
│   └── exceptions/
│       ├── invalid_score_error.py
│       └── invalid_filter_config_error.py
│
├── application/                      # Orquestació — només coneix interfícies (ports)
│   ├── dtos/
│   │   ├── scored_tender_dto.py      # DTO de sortida: total, detall, recomendacio, created_at, documents
│   │   └── report_dto.py             # DTO de sortida: llista ScoredTenderDTO + totals
│   ├── ports/                        # ABCs per a la infraestructura
│   │   ├── tender_api_port.py        # Accés a l'API externa de contractació
│   │   ├── tender_repository_port.py # CRUD de Tender a BD (save, list_all, is_duplicate, count, update_score)
│   │   ├── filter_repository_port.py # CRUD de FilterConfig a BD
│   │   ├── nlp_analyser_port.py      # Anàlisi NLP de documents (amb filenames optatiu)
│   │   ├── document_storage_port.py  # Guardat/llistat/esborrat de PDFs a disc (J.4)
│   │   └── tender_document_repository_port.py  # Persistència de TenderDocument a BD (J.5)
│   ├── use_cases/
│   │   ├── fetch_candidates_use_case.py  # Descàrrega paginada automàtica des de count() (H.2)
│   │   └── run_pipeline_use_case.py      # Orquestra: fetch→save+flush→disc→BD docs→NLP→score→commit
│   └── exceptions/
│       └── application_errors.py
│
└── infrastructure/                   # Implementacions concretes
    ├── database.py                   # SQLAlchemy engine + SessionLocal
    ├── dependencies.py               # FastAPI Depends factories
    ├── models/                       # ORM models (mapeig BD ↔ Python)
    │   ├── tender_model.py           # Taula tenders (inclou score_*, recomendacio, created_at)
    │   ├── tender_document_model.py  # Taula tender_documents (J.1)
    │   └── filter_config_model.py    # Taula filter_configs
    ├── api/                          # Routers FastAPI
    │   ├── pipeline_router.py        # POST /api/v1/pipeline/run · GET /api/v1/pipeline/status
    │   ├── filters_router.py         # GET/POST /api/v1/filters · GET /api/v1/filters/active
    │   ├── tenders_router.py         # GET /api/v1/tenders · GET /api/v1/tenders/{id}
    │   ├── documents_router.py       # GET …/download · DELETE … (J.7)
    │   ├── ui_router.py              # Pàgines HTML: / · /licitacions · /filtres
    │   └── exception_handlers.py     # Gestors globals d'excepcions
    ├── repositories/
    │   ├── sqlalchemy_tender_repository.py          # save, list_all, is_duplicate, count, update_score
    │   ├── sqlalchemy_tender_document_repository.py # save, list_by_expedient (J.5)
    │   └── sqlalchemy_filter_repository.py          # save, get_active
    └── services/
        ├── contractacio_publica_client.py  # HTTP client amb reintentos + paginació; filtra ALERTA_FUTURA
        ├── timbal_nlp_analyser.py          # LiteLLM config-driven (G.3); pymupdf per a text ≤32k chars
        └── local_file_document_storage.py  # Escriu PDFs a downloads/<expedient_id>/ (J.4)
```

---

## Capes i responsabilitats

### Domini `app/domain/`
Nucli de l'app. Sense dependències externes. Totes les regles de negoci (RN-03, RN-05, RN-12…) viuen aquí.

- **Entities:** `Tender`, `Document`, `ScoredTender`, `ComparativeReport`, `TenderDocument`, `DocumentAnalysis`
- **Value Objects:** `FilterConfig` (amb `to_api_params()`), `Score` (0–100 + semàfor + detall 5 criteris), `TrafficLight`, `DocumentType`
- **Exceptions:** `InvalidScoreError`, `InvalidFilterConfigError`

> `Score` treballa en escala 0–100. Semàfor: verd ≥70 / groc 40–69 / vermell <40 (RN-03, RN-12).

### Aplicació `app/application/`
Orquestra el domini. Només coneix interfícies (ports), mai implementacions concretes.

- **DTOs:** `ScoredTenderDTO` (total, detall, recomendacio, created_at, documents), `ReportDTO`
- **Ports:** `TenderApiPort`, `TenderRepositoryPort`, `FilterRepositoryPort`, `NlpAnalyserPort`, `DocumentStoragePort`, `TenderDocumentRepositoryPort`
- **Use Cases:**
  - `FetchCandidatesUseCase` — paginació automàtica: `page = count() // max_licitacions`, evita duplicats (H.2)
  - `RunPipelineUseCase` — fetch → `save(tender)` + `flush()` → disc → BD docs → NLP → `update_score()` → `commit()`

### Infraestructura `app/infrastructure/`
Implementacions concretes. Depèn de l'aplicació, mai al revés.

- **API REST JSON:** routers a `app/infrastructure/api/` (prefix `/api/v1`)
- **UI HTML:** `ui_router.py` — Dashboard, Licitacions (llegeix de BD directament), Filtres
- **HTTP Client:** `ContractacioPublicaClient` — HTTP amb reintentos + paginació; descarta ítems `ALERTA_FUTURA` (RN-15)
- **NLP:** `TimbalNlpAnalyser` — detecta provider LiteLLM; `google`/`anthropic` → PDF natiu; resta → text via `pymupdf` truncat a 32k chars (G.3)
- **Storage:** `LocalFileDocumentStorage` — escriu PDFs a `downloads/<expedient_id>/<filename>` (J.4)
- **Repositories:** SQLAlchemy ORM + `session.flush()` garanteix FKs `tender_documents → tenders` (PostgreSQL)

---

## Flux del pipeline

```
FilterConfig.to_api_params() → GET /cerca-avancada (API)
  ↓ per cada licitació (is_duplicate() == False)
  → GET /detall-publicacio-expedient/{expedientId}/{publicacioId}
    → GET /descarrega-document/{docId}/{hash} → bytes PDF
  → repository.save(tender) + session.flush()           ← FK garantida
  → LocalFileDocumentStorage.save()                     ← disc: downloads/<id>/
  → SqlAlchemyTenderDocumentRepository.save(doc)        ← BD
  → TimbalNlpAnalyser.analyse(pdfs, filenames)          ← LLM (provider-aware)
  → Score (0–100) + TrafficLight + comentaris_per_doc + recomendacio
  → repository.update_score(tender, score, recomendacio, created_at)
  → db.commit()
  → ReportDTO → /licitacions (llegeix de BD)
```

---

## TDD
Cada capa es prova de forma aïllada:
- **Domini:** tests unitaris purs, sense mocks
- **Aplicació:** mocks dels ports
- **Infraestructura:** tests d'integració contra serveis reals o contenidors Docker

---

## API REST (FastAPI)

Base JSON API: `/api/v1`  ·  UI (HTML): sense prefix

### Pipeline
| Mètode | Endpoint | Descripció |
|---|---|---|
| `POST` | `/api/v1/pipeline/run` | Llança el pipeline complet (background task) |
| `GET` | `/api/v1/pipeline/status` | Estat del pipeline en curs (RNF-01) |

### Filtres
| Mètode | Endpoint | Descripció |
|---|---|---|
| `GET` | `/api/v1/filters` | Historial de configuracions de filtre |
| `POST` | `/api/v1/filters` | Crea nova FilterConfig i l'activa |
| `GET` | `/api/v1/filters/active` | Configuració activa actual |

### Licitacions
| Mètode | Endpoint | Descripció |
|---|---|---|
| `GET` | `/api/v1/tenders` | Llista licitacions processades amb semàfor |
| `GET` | `/api/v1/tenders/{id}` | Detall d'una licitació |

### Documents
| Mètode | Endpoint | Descripció |
|---|---|---|
| `GET` | `/api/v1/documents/{expedient_id}/{filename}/download` | Descàrrega PDF (RF-09) |
| `DELETE` | `/api/v1/documents/{expedient_id}/{filename}` | Esborra de disc i BD |

### UI (HTML)
| Mètode | Endpoint | Descripció |
|---|---|---|
| `GET` | `/` | Dashboard — estat del pipeline |
| `GET` | `/licitacions` | Panel comparativa (RF-07) — llegeix de BD |
| `GET` | `/filtres` | Formulari de configuració de filtres |

---

## Model de dades (PostgreSQL)

### Taula `tenders`
| Columna | Tipus | Notes |
|---|---|---|
| `id` | UUID (PK) | `expedient_id` |
| `publicacio_id` | INTEGER | |
| `organ` | VARCHAR | |
| `titol` | VARCHAR | |
| `codi_expedient` | VARCHAR nullable | |
| `pressupost` | FLOAT nullable | |
| `cpv_principal` | VARCHAR nullable | |
| `data_limit` | TIMESTAMP nullable | Termini de presentació |
| `durada_dies` | INTEGER nullable | |
| `tipus_contracte_id` | INTEGER nullable | |
| `procediment_id` | INTEGER nullable | |
| `nuts_code` | VARCHAR nullable | Codi NUTS del lloc d'execució |
| `classifications` | JSON | Grups de classificació empresarial |
| `score_total` | INTEGER nullable | 0–100 (J.1) |
| `score_traffic_light` | VARCHAR nullable | green/yellow/red (J.1) |
| `score_detall` | JSON nullable | Desglose 5 criteris RN-12 (J.1) |
| `recomendacio` | TEXT nullable | GO/NO GO generat pel LLM (J.1) |
| `created_at` | TIMESTAMP | Data de processament pel pipeline (J.1) |

### Taula `tender_documents`
| Columna | Tipus | Notes |
|---|---|---|
| `id` | INTEGER (PK) | autoincremental |
| `expedient_id` | UUID (FK → tenders.id) | |
| `filename` | VARCHAR | Nom del fitxer PDF |
| `filepath` | VARCHAR | Ruta relativa al disc |
| `comentari_llm` | TEXT nullable | Comentari NLP per document (J.1) |
| `created_at` | TIMESTAMP | Data de creació del registre |

### Taula `filter_configs`
| Columna | Tipus | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `is_active` | BOOLEAN | Només 1 activa alhora |
| `fase_vigent` | INTEGER | Default 30 (Anunci licitació, RN-14) |
| `tipus_contracte` | INTEGER | Default 395 (Obres) |
| `procediment_adjudicacio` | INTEGER | Default 401 (Obert) |
| `ambit` | INTEGER | Default 1500001 (Generalitat de Catalunya) |
| `max_licitacions` | INTEGER | 1–100, default 20 (RN-13) |
| ... | ... | Tots els camps de `FilterConfig` |
