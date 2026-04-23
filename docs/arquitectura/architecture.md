# Arquitectura

## Stack
- **Lenguaje:** Python
- **API REST:** FastAPI
- **Workflow / Agentes:** Timbal
- **Base de datos:** PostgreSQL
- **Fuente de datos:** contractaciopublica.cat

---

## Estructura de carpetas

```
app/
├── domain/
│   ├── entities/
│   │   ├── tender.py
│   │   ├── document.py
│   │   ├── scored_tender.py
│   │   └── comparative_report.py
│   ├── value_objects/
│   │   ├── filter_config.py
│   │   ├── score.py
│   │   ├── requirements.py
│   │   ├── traffic_light.py          # Enum
│   │   └── document_type.py          # Enum
│   ├── events/
│   │   ├── tender_downloaded_event.py
│   │   ├── evaluation_completed_event.py
│   │   └── process_failed_event.py
│   └── exceptions/
│       ├── download_error.py
│       ├── filter_validation_error.py
│       ├── duplicate_tender_error.py
│       └── expired_tender_error.py
│
├── application/
│   ├── dtos/
│   │   ├── tender_dto.py
│   │   ├── document_dto.py
│   │   ├── score_dto.py
│   │   └── filter_config_dto.py
│   ├── ports/
│   │   ├── licitation_api_port.py
│   │   ├── tender_repository_port.py
│   │   ├── document_storage_port.py
│   │   └── notification_port.py
│   └── use_cases/
│       ├── commands/
│       │   ├── download_tenders_command.py
│       │   ├── filter_tenders_command.py
│       │   └── score_tender_command.py
│       └── queries/
│           ├── get_scored_tenders_query.py
│           └── get_comparative_report_query.py
│
└── infrastructure/
    ├── api/
    │   └── v1/
    │       ├── main.py               # FastAPI app
    │       ├── routers/
    │       │   ├── pipeline_router.py
    │       │   ├── filters_router.py
    │       │   ├── reports_router.py
    │       │   └── tenders_router.py
    │       └── schemas/              # Pydantic request/response models
    │           ├── pipeline_schema.py
    │           ├── filter_schema.py
    │           ├── report_schema.py
    │           └── tender_schema.py
    ├── repositories/
    │   ├── tender_repository.py
    │   └── document_repository.py
    └── services/
        ├── contractacio_publica_client.py
        ├── nlp_service.py
        ├── email_service.py
        ├── download_monitor.py
        └── retry_manager.py
```

---



### Dominio `app/domain/`
Núcleo de la app. Sin dependencias externas.

- **Entities:** `Tender`, `Document`, `ScoredTender`, `ComparativeReport`
- **Value Objects:** `FilterConfig`, `Score`, `Requirements`
- **Enums:** `DocumentType`, `TrafficLight`
- **Events:** `TenderDownloadedEvent`, `EvaluationCompletedEvent`, `ProcessFailedEvent`
- **Exceptions:** `DownloadError`, `FilterValidationError`, `DuplicateTenderError`, `ExpiredTenderError`

### Aplicación `app/application/`
Orquesta el dominio. Solo conoce interfaces, nunca implementaciones.

- **DTOs:** `TenderDTO`, `DocumentDTO`, `ScoreDTO`, `FilterConfigDTO`
- **Ports:** `LicitationApiPort`, `TenderRepositoryPort`, `DocumentStoragePort`, `NotificationPort`
- **Commands:** `DownloadTendersCommand`, `FilterTendersCommand`, `ScoreTenderCommand`
- **Queries:** `GetScoredTendersQuery`, `GetComparativeReportQuery`

### Infraestructura `app/infrastructure/`
Implementaciones concretas. Depende de la aplicación, nunca al revés.

- **API REST:** routers FastAPI `app/infrastructure/api/v1/`
- **HTTP Client:** `ContractacioPublicaClient` (HTTP + reintentos + paginación)
- **Repositories:** `TenderRepository`, `DocumentRepository` (PostgreSQL)
- **Services:** `NlpService` (extracción), `EmailService` (notificaciones)
- **Monitoring:** `DownloadMonitor`, `RetryManager`

---

## Flujo del pipeline

```
FilterConfig → DownloadTenders → FilterTenders → DownloadDocuments
            → ExtractRequirements → ScoreTender → ComparativeReport → Notify
```

---

## TDD
Cada capa se prueba de forma aislada:
- **Dominio:** tests unitarios puros, sin mocks
- **Aplicación:** mocks de los ports
- **Infraestructura:** tests de integración contra servicios reales o contenedores

---

## API REST (FastAPI)

Base: `/api/v1`

### Pipeline
| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/pipeline/run` | Lanza el proceso completo (descarga + filtrado + puntuación) |
| `GET` | `/pipeline/status` | Estado del proceso en curso (RNF-01) |

### Filtros
| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/filters` | Obtiene la configuración de filtros activa |
| `PUT` | `/filters` | Actualiza los filtros antes de lanzar el pipeline (R-05) |

### Resultados
| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/reports` | Lista los informes comparativos generados |
| `GET` | `/reports/{id}` | Detalle de un informe (RF-07) |
| `GET` | `/tenders` | Lista de licitaciones evaluadas con su semáforo |
| `GET` | `/tenders/{id}` | Detalle de una licitación evaluada |
