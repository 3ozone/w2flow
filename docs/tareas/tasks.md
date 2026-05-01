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

---

## Fase 7 — Mejoras y fixes post-validación

### 7.1 Logging modo debug configurable

- [x] Añadir `logging.basicConfig` en `main.py` condicionado a `settings.app_debug`
- [x] Logs HTTP cliente (`ContractacioPublicaClient`) en nivel `debug`
- [x] Logs descarga documentos (`DownloadDocumentsCommandHandler`) en nivel `debug`/`info` según criticidad

### 7.2 Descarga de todos los documentos sin filtro UNKNOWN

- [x] Eliminar el bloque `if doc_type == DocumentType.UNKNOWN: continue` de `DownloadDocumentsCommandHandler`
- [x] `DocumentType` se sigue calculando para clasificación futura, pero ya no actúa como filtro

### 7.3 DocumentRepository escribe también en disco

- [x] `TEST` `DocumentRepository` — nuevos tests verifican escritura en disco (`test_save_writes_bytes_to_disk`, `test_save_returns_disk_path`, `test_save_overwrites_file_on_duplicate`)
- [x] `IMPL` `DocumentRepository` — acepta `base_dir`, escribe bytes PDF en `base_dir/expedient_id/titol`, guarda el path real en DB
- [x] `IMPL` `dependencies.py` — sustituir `LocalDocumentStorage` por `DocumentRepository` con `base_dir=settings.download_dir`

---

## Fase 8 — Nuevos endpoints

### 8.1 GET /tenders/{id}/documents — listar documentos de un expediente

> Los documentos ya se guardan en DB (`DocumentRepository`). Falta exponerlos via API.

- [x] `TEST` `tenders_router` — `GET /tenders/{id}/documents` devuelve lista de `DocumentSchema` con los docs del expediente; devuelve 404 si el tender no existe
- [x] `IMPL` `DocumentSchema` — schema Pydantic con `doc_id`, `titol`, `type`, `mida_kb`, `file_path`
- [x] `IMPL` `DocumentStoragePort` — añadir método `list_by_expedient(expedient_id) -> list[Document]`
- [x] `IMPL` `DocumentRepository.list_by_expedient` — query a DB filtrando por `expedient_id`
- [x] `IMPL` `tenders_router` — endpoint `GET /tenders/{id}/documents`

### 8.2 GET /tenders/{id}/documents/{doc_id}/download — descargar PDF

> El fichero está en disco. El endpoint lo sirve como `application/pdf`.

- [x] `TEST` `tenders_router` — `GET /tenders/{id}/documents/{doc_id}/download` devuelve `FileResponse` con el PDF; 404 si no existe
- [x] `IMPL` `tenders_router` — endpoint `GET /tenders/{id}/documents/{doc_id}/download` usando `FileResponse`

### 8.3 DELETE /tenders/{id} — eliminar un tender

- [x] `TEST` `tenders_router` — `DELETE /tenders/{id}` devuelve 204; un segundo DELETE devuelve 404
- [x] `IMPL` `TenderRepositoryPort` — añadir método `delete(expedient_id: str) -> None`
- [x] `IMPL` `TenderRepository.delete` — borra el tender y sus scores/documentos en cascada
- [x] `IMPL` `tenders_router` — endpoint `DELETE /tenders/{id}`

### 8.4 DELETE /reports/{id} — eliminar un report del store

- [x] `TEST` `reports_router` — `DELETE /reports/{id}` devuelve 204; un segundo DELETE devuelve 404
- [x] `IMPL` `reports_router` — endpoint `DELETE /reports/{id}` que borra de `_reports` y `_reports_analysis`

### 8.5 GET /health — health check

- [x] `TEST` `health_router` — `GET /health` devuelve `{"status": "ok"}` con HTTP 200
- [x] `IMPL` `health_router` — router con `GET /health`; comprueba conexión a DB e incluye estado en la respuesta
- [x] `IMPL` `main.py` — registrar `health_router`

---

## Fase 9 — Frontend (HTMX + Jinja2)

> Stack: **Jinja2** para templates server-side, **HTMX** vía CDN para interactividad sin build step, **TailwindCSS** vía CDN para estilos.
> FastAPI sirve las páginas HTML mediante `Jinja2Templates`. Los endpoints REST existentes no se modifican.

### 9.0 Setup

- [x] `IMPL` añadir `jinja2` a `pyproject.toml`
- [x] `IMPL` crear estructura `app/templates/` y `app/static/`
- [x] `IMPL` `main.py` — montar `StaticFiles` en `/static` y configurar `Jinja2Templates`
- [x] `IMPL` `app/templates/base.html` — layout base con HTMX + TailwindCSS vía CDN, navbar

### 9.1 Página principal — Dashboard

- [x] `IMPL` `app/templates/index.html` — extiende `base.html`; muestra: badge health, filtro activo, botón "Ejecutar Pipeline", estado del pipeline con polling automático
- [x] `IMPL` `app/templates/partials/pipeline_status.html` — fragmento HTML con estado (IDLE/RUNNING/DONE/ERROR) + barra de progreso; se refresca con `hx-trigger="every 2s"` mientras está RUNNING
- [x] `IMPL` router `ui_router.py` — `GET /` sirve `index.html`; `GET /partials/pipeline-status` devuelve el partial

### 9.2 Página de tenders

- [x] `IMPL` `app/templates/tenders.html` — tabla de tenders con semáforo (🟢🟡🔴), presupuesto, órgano, fecha; cada fila tiene botón expandir para ver documentos
- [x] `IMPL` `app/templates/partials/tender_documents.html` — lista de documentos con nombre, tipo, tamaño y enlace de descarga PDF; cargado con `hx-get` al expandir
- [x] `IMPL` `ui_router.py` — `GET /tenders` sirve `tenders.html`; `GET /partials/tenders/{id}/documents` devuelve el partial de documentos

### 9.3 Página de reports

- [x] `IMPL` `app/templates/reports.html` — lista de reports con fecha, nº tenders viables/total; cada report tiene enlace a detalle
- [x] `IMPL` `app/templates/report_detail.html` — detalle de un report: tabla de tenders puntuados + sección colapsable con análisis narrativo de Gemini
- [x] `IMPL` `ui_router.py` — `GET /reports` sirve `reports.html`; `GET /reports/{id}` sirve `report_detail.html`

### 9.4 Página de configuración de filtros

- [x] `IMPL` `app/templates/filters.html` — formulario con los campos de `FilterSchema` (presupuesto mínimo, keywords positivos/negativos, tipo expediente, fase); submit con `hx-put` a `/api/v1/filters`
- [x] `IMPL` `ui_router.py` — `GET /filters` sirve `filters.html`

### 9.5 Integración final

- [x] `IMPL` `main.py` — registrar `ui_router` sin prefijo `/api/v1`
- [x] Validar flujo completo: configurar filtro → ejecutar pipeline → ver tenders → descargar PDF → leer análisis Gemini
