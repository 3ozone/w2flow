# TASKS — w2flow

Backlog ordenado por orden de implementación siguiendo Clean Architecture (dominio primero) y flujo TDD del AGENTS.md.

**Flujo por tarea:** `TEST` → `EXCEPCIÓN` (si aplica) → `IMPL` → `✅ TESTS GREEN`

Leyenda: `[ ]` pendiente · `[x]` completado · `[~]` en progreso

---

## Fase 0 — Setup del proyecto
> Sin TDD — son tareas de configuración

- [x] Inicializar estructura de carpetas (`domain/`, `application/`, `infrastructure/`, `tests/`)
- [x] Configurar `pyproject.toml` con dependencias (FastAPI, SQLAlchemy, Pydantic, Alembic, pytest)
- [x] Configurar variables de entorno (`.env` + `Settings` con Pydantic)
- [x] Configurar PostgreSQL con Docker Compose (desarrollo local)
- [x] Configurar pytest con estructura espejo de `app/`
- [ ] Crear `Dockerfile` + `.dockerignore` para la app
- [ ] Crear manifiestos Kubernetes básicos (`deployment.yaml`, `service.yaml`, `configmap.yaml`, `secret.yaml`)

> **Nota despliegue**: La app se contenerizará con Docker y desplegará en Kubernetes.
> Las variables de entorno en producción se inyectan vía `ConfigMap` y `Secret` de K8s — no se usa `.env` en el contenedor.
> `pydantic-settings` lee las vars del entorno del sistema con prioridad sobre el `.env`, por lo que `app/config.py` es compatible con ambos entornos sin cambios.

---

## Fase 1 — Dominio

### 1.1 Enums
> Sin excepciones ni tests complejos — son tipos fijos

- [x] `TEST` `DocumentType` — valores PCAP, PPT, TECHNICAL_MEMORY, BUDGET, ANNEXES, UNKNOWN + `from_title()` con titols reales de la API
- [x] `IMPL` `DocumentType` (Enum con `from_title(titol: str)`)
- [x] `TEST` `TrafficLight` — valores GREEN, YELLOW, RED y umbrales (≥50=GREEN, ≥25=YELLOW, <25=RED)
- [x] `IMPL` `TrafficLight` (Enum)

### 1.2 Value Objects

- [x] `TEST` `FilterConfig` — `toApiParams()` genera los params correctos para la API, `matches()` con tender válido e inválido por importe
- [x] `EXCEPCIÓN` `FilterValidationError`
- [x] `IMPL` `FilterConfig` (frozen dataclass con `tipusExpedient`, `faseVigent`, `maxResults`, `sectorKeywords`, `minPressupost`)

- [x] `TEST` `Score` — `assignTrafficLight()` con total 55/30/10, `isViable()` retorna False si total<25, `toReport()` estructura correcta
- [x] `IMPL` `Score` (frozen dataclass con `expedientId`, `total`, `detall`, `paraulesClauTrobades`, `penalitzacions`, `recomanacio`)

- [x] `TEST` `Requirements` — `isEmpty()` con y sin datos, `toDict()` estructura correcta
- [x] `IMPL` `Requirements` (frozen dataclass con `expedientId`, `solvencyRequirements`, `technicalRequirements`, `adjudicationCriteria`, `specialClauses`, `rawAgentOutput`)

### 1.3 Entidades

- [x] `TEST` `Tender` — `isNew()` con fecha hoy vs ayer, `getBasicInfo()` contiene campos API reales (`expedientId`, `titol`, `organ`, `pressupost`), igualdad por `expedientId`
- [x] `EXCEPCIÓN` `ExpiredTenderError`
- [x] `IMPL` `Tender` (Entity con campos `expedientId`, `publicacioId`, `titol`, `organ`, `pressupost`, `codiExpedient`, `fase`, `dataPublicacio`)

- [x] `TEST` `Document` — `isValidType()` True si type != UNKNOWN, identidad por `(expedientId, docId)`
- [x] `EXCEPCIÓN` `DuplicateTenderError`
- [x] `IMPL` `Document` (Entity con campos `expedientId`, `docId`, `titol`, `hash`, `midaKb`, `filePath`, `type`)

- [x] `TEST` `ScoredTender` — `isGo()` delega en `score.isViable()`, `getSummary()` estructura
- [x] `IMPL` `ScoredTender` (Entity)

- [x] `TEST` `ComparativeReport` — `getViableTenders()` filtra correctamente, `generateJSON()` estructura
- [x] `IMPL` `ComparativeReport` (Entity)

### 1.4 Eventos

- [x] `IMPL` `TenderDownloadedEvent`
- [x] `IMPL` `EvaluationCompletedEvent`
- [x] `IMPL` `ProcessFailedEvent`

---

## Fase 2 — Aplicación

### 2.1 DTOs

- [x] `TEST` `FilterConfigDTO` — conversión desde/hacia `FilterConfig`
- [x] `IMPL` `FilterConfigDTO`

- [x] `TEST` `TenderDTO` — conversión desde/hacia `Tender`
- [x] `IMPL` `TenderDTO`

- [x] `TEST` `DocumentDTO` — conversión desde/hacia `Document`
- [x] `IMPL` `DocumentDTO`

- [x] `TEST` `ScoreDTO` — conversión desde/hacia `Score`
- [x] `IMPL` `ScoreDTO`

### 2.2 Ports (interfaces ABC)
> Sin tests — son contratos, se testean a través de sus implementaciones

- [x] `IMPL` `LicitationApiPort`
- [x] `IMPL` `TenderRepositoryPort`
- [x] `IMPL` `DocumentStoragePort`
- [x] `IMPL` `NotificationPort`

### 2.3 Commands

- [x] `TEST` `DownloadTendersCommandHandler` — mock de `LicitationApiPort`, descarga y filtra por fecha
- [x] `EXCEPCIÓN` `DownloadError`
- [x] `IMPL` `DownloadTendersCommandHandler`

- [x] `TEST` `FilterTendersCommandHandler` — mock de port, aplica `FilterConfig.matches()`
- [x] `IMPL` `FilterTendersCommandHandler`

- [x] `TEST` `ScoreTenderCommandHandler` — mock de ports, genera `ScoredTender` con score correcto
- [x] `IMPL` `ScoreTenderCommandHandler`

### 2.4 Queries

- [x] `TEST` `GetScoredTendersQueryHandler` — mock de repositorio, devuelve lista paginada
- [x] `IMPL` `GetScoredTendersQueryHandler`

- [x] `TEST` `GetComparativeReportQueryHandler` — mock de repositorio, devuelve informe por id
- [x] `IMPL` `GetComparativeReportQueryHandler`

---

## Fase 3 — Infraestructura

### 3.1 Base de datos

- [x] `TEST` Modelos SQLAlchemy — mapeo correcto a tablas
- [x] `IMPL` `TenderModel`, `DocumentModel`, `ScoreModel`
- [x] `IMPL` Migraciones Alembic (creación de tablas)

- [x] `TEST` `TenderRepository` — integración contra PostgreSQL (pytest + fixtures)
- [x] `IMPL` `TenderRepository` (implementa `TenderRepositoryPort`)

- [x] `TEST` `DocumentRepository` — integración, comprueba deduplicación (RN-06)
- [x] `IMPL` `DocumentRepository` (implementa `DocumentStoragePort`)

### 3.2 Cliente externo

- [x] `TEST` `RetryManager` — 2 reintentos, backoff, lanza error al tercer fallo (R-04)
- [x] `IMPL` `RetryManager`

- [x] `TEST` `ContractacioPublicaClient` — mock HTTP, paginación, autenticación
- [x] `IMPL` `ContractacioPublicaClient` (implementa `LicitationApiPort`)

- [x] `IMPL` `DownloadMonitor` (progreso y registro de errores)

### 3.3 Servicios

- [x] `TEST` `NlpService` — extracción de requisitos desde documento de prueba
- [x] `IMPL` `NlpService` (Timbal)

- [x] `TEST` `EmailService` — mock SMTP, verifica llamada con contenido correcto
- [x] `IMPL` `EmailService` (implementa `NotificationPort`)

---

## Fase 4 — API REST (FastAPI)

### 4.1 Schemas Pydantic

- [x] `TEST` `FilterSchema` — validación de campos obligatorios
- [x] `IMPL` `FilterSchema`, `TenderSchema`, `ReportSchema`, `PipelineStatusSchema`

### 4.2 Routers

- [x] `TEST` `pipeline_router` — `POST /pipeline/run` lanza command, `GET /pipeline/status` devuelve estado
- [x] `IMPL` `pipeline_router`

- [x] `TEST` `filters_router` — `GET` devuelve config activa, `PUT` valida y actualiza
- [x] `IMPL` `filters_router`

- [x] `TEST` `tenders_router` — `GET /tenders` lista, `GET /tenders/{id}` detalle y 404
- [x] `IMPL` `tenders_router`

- [x] `TEST` `reports_router` — `GET /reports` lista, `GET /reports/{id}` detalle y 404
- [x] `IMPL` `reports_router`

### 4.3 App principal

- [x] `IMPL` `main.py` — setup FastAPI, routers, manejo de errores global

---

## Fase 5 — Validación final

- [x] Test end-to-end del pipeline completo con datos reales
- [x] Validar tiempo de ejecución < 1 minuto (R-03)
- [x] Validar deduplicación de licitaciones (RN-06)
- [x] Validar descarte de licitaciones expiradas (RN-05)
- [x] `README.md` con instrucciones de setup y ejecución

---

## Fase 6 — Integración completa del pipeline

> Conectar los servicios ya implementados al flujo real de ejecución.

### 6.0 REFACTOR — Extraer lógica del pipeline a `RunPipelineCommandHandler`

> **Violaciones detectadas en 6.1** que deben corregirse antes de continuar:
> 1. `pipeline_router.py` instancia `ComparativeReport` (entidad de dominio) directamente — presentación no debe crear entidades de dominio.
> 2. `pipeline_router.py` accede a `reports_router._reports` directamente — un router no debe acceder al estado interno de otro router.
>
> **Solución**: Mover la orquestación completa del pipeline a `RunPipelineCommandHandler` (aplicación). El router solo llama al handler y recibe el `ComparativeReport` como resultado.

- [x] `TEST` `RunPipelineCommandHandler` — mock de todos los ports, valida que orquesta download→filter→score→report y devuelve `ComparativeReport`
- [x] `IMPL` `RunPipelineCommandHandler` en `application/use_cases/commands/` — recibe `LicitationApiPort`, `TenderRepositoryPort`, `FilterConfig`; devuelve `ComparativeReport`
- [x] `REFACTOR` `pipeline_router.py` — sustituir la lógica interna por una llamada a `RunPipelineCommandHandler`; guardar el report en `reports_router` mediante un método público `add_report()` en vez de acceso directo a `_reports`
- [x] `TEST` `pipeline_router` — verificar que el comportamiento observable (POST /pipeline/run → GET /reports devuelve 1 informe) se mantiene tras el refactor

### 6.1 ComparativeReport tras pipeline (RF-07)

- [x] `TEST` `pipeline_router` — tras completar, `GET /reports` devuelve 1 informe con los tenders puntuados
- [x] `IMPL` `pipeline_router._run_pipeline` — crear `ComparativeReport` con los `ScoredTender` y almacenarlo en `reports_router._reports`

### 6.2 Fetch de detalle para presupuesto real (RF-02)

- [x] `TEST` `ContractacioPublicaClient.fetch_detail` — mock HTTP, devuelve `pressupostLicitacio` real
- [x] `IMPL` `ContractacioPublicaClient.fetch_detail(publicacio_id)` — `GET /cerca-avancada/{id}` y retorna el item de detalle
- [x] `TEST` `DownloadTendersCommandHandler` — cuando la API de listado devuelve `pressupostLicitacio=null`, hace fetch del detalle y usa el presupuesto real
- [x] `IMPL` `DownloadTendersCommandHandler` — llamar a `fetch_detail` cuando `pressupostLicitacio` es `null`

### 6.3 Descarga de documentos PDF + NLP (RF-04, RF-05)

- [x] `TEST` `ContractacioPublicaClient.fetch_documents` — mock HTTP, devuelve lista de documentos adjuntos de una licitación
- [x] `IMPL` `ContractacioPublicaClient.fetch_documents(expedient_id)` — endpoint de documentos adjuntos (DFS recursivo sobre `dades`)
- [x] `TEST` `DownloadDocumentsCommandHandler` — descarga PDFs filtrados por `DocumentType`, guarda con `DocumentStoragePort`
- [x] `IMPL` `DownloadDocumentsCommandHandler`
- [x] `TEST` `pipeline_router` — el pipeline llama a `DownloadDocumentsCommandHandler` y pasa los textos PDF al `ScoreTenderCommandHandler`
- [x] `IMPL` `pipeline_router._run_pipeline` — etapa de descarga de documentos antes del scoring

### 6.4 Lectura de texto PDF con pymupdf + scoring real (RF-05, RF-06)

> **Clean Architecture**: `PdfExtractorPort` (aplicación) se define antes que la implementación (infraestructura). `DownloadDocumentsCommandHandler` depende solo del puerto, nunca de pymupdf.

- [x] `IMPL` `pymupdf` en `pyproject.toml` (nueva dependencia)
- [x] `IMPL` `PdfExtractorPort` — puerto ABC en `application/ports/` con método `extract_text(pdf_bytes: bytes) -> str`
- [x] `TEST` `PdfTextExtractor` — dado un fichero PDF en bytes, devuelve el texto concatenado de todas las páginas
- [x] `IMPL` `PdfTextExtractor` — servicio en `infrastructure/services/` que implementa `PdfExtractorPort` usando `pymupdf`
- [x] `TEST` `ScoreTenderCommandHandler` — cuando recibe `pdf_texts` no vacíos, el scoring usa el contenido del PDF además del título
- [x] `IMPL` `ScoreTenderCommandHandler` — ya pasa `pdf_texts` al `_calculate_score`; verificar que funciona con texto real

### 6.5 Agente Timbal análisis comparativo (RF-07)

> **Clean Architecture**: `AnalysisPort` (aplicación) se define antes que la implementación (infraestructura). `NlpService` ya existe para extraer `Requirements` estructurados — `AnalysisService` es una responsabilidad distinta (análisis narrativo comparativo) y NO la reemplaza.

- [x] `IMPL` `AnalysisPort` — puerto ABC en `application/ports/` con método `analyze(scored_tenders: list[ScoredTender], pdf_paths: list[str]) -> str`
- [x] `TEST` `AnalysisService` — mock del agente Timbal, devuelve texto formateado dado lista de `ScoredTender` + rutas PDF
- [x] `IMPL` `AnalysisService` — servicio en `infrastructure/services/` que implementa `AnalysisPort`; usa Timbal con `SYSTEM_PROMPT` del `tender_downloader.py`
- [x] `TEST` `pipeline_router` — tras completar, el texto del agente se guarda en `reports_router._reports_analysis[report_id]`
- [x] `IMPL` `pipeline_router._run_pipeline` — llamar a `AnalysisPort` tras el scoring; guardar resultado en `reports_router._reports_analysis` (separado de `ComparativeReport`)

### 6.6 Configuración: pymupdf + GEMINI_API_KEY

- [x] `IMPL` añadir `pymupdf>=1.24` a `pyproject.toml`
- [x] `IMPL` añadir `gemini_api_key: str = ""` a `app/config.py`
- [x] `IMPL` `GEMINI_API_KEY` disponible vía variable de entorno del sistema (pydantic-settings la lee automáticamente; Timbal también la usa directamente del OS env)

### 6.7 LocalDocumentStorage (RF-04)

- [x] `TEST` `LocalDocumentStorage` — guarda bytes PDF en disco bajo `downloads/{expedient_id}/{titol}`, devuelve la ruta
- [x] `IMPL` `LocalDocumentStorage` — implementa `DocumentStoragePort` usando filesystem local
- [x] `IMPL` añadir `download_dir: str = "downloads"` a `app/config.py`

### 6.8 Endpoint análisis narrativo (RF-07)

> **Clean Architecture**: El texto del agente NO va en `ComparativeReport` (dominio puro). Se almacena en `reports_router._reports_analysis: dict[str, str]` (estado de presentación). `ComparativeReport` no cambia.

- [x] `IMPL` `reports_router` — añadir `_reports_analysis: dict[str, str] = {}` como estado del módulo
- [x] `TEST` `reports_router` — `GET /reports/{id}/analysis` devuelve `{"analysis": "..."}` o 404 si el id no existe en `_reports_analysis`
- [x] `IMPL` `reports_router` — añadir endpoint `GET /reports/{id}/analysis`
- [x] `IMPL` `AnalysisSchema` — schema Pydantic `{"analysis": str}` para la respuesta (`_AnalysisResponse` inline en reports_router)
