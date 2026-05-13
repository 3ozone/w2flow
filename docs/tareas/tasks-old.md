# TASKS — w2flow

Backlog ordenado por orden de implementación siguiendo Clean Architecture (dominio primero) y flujo TDD del AGENTS.md.

**Flujo por tarea:** `TEST` → `EXCEPCIÓN` (si aplica) → `IMPL` → `✅ TESTS GREEN`

Leyenda: `[ ]` pendiente · `[x]` completado · `[~]` en progreso

---

## 🚨 Fase 11 — Corrección de RFs (PRIORIDAD MÁXIMA)

> Desviaciones detectadas en la auditoría de requisitos. Se implementan antes de cualquier otra fase.
> Orden de implementación: RF-05 → RF-06 → RF-03 → RF-02/RF-04

### 11.1 RF-05 — Alimentar PDFs al scorer y al agente Gemini

> **Problema**: Los PDFs se descargan a disco pero `RunPipelineCommandHandler` llama a `ScoreTenderCommand(pdf_texts=[])` y `AnalysisService(pdf_paths=[])` con listas vacías.
> **Solución**: Leer los bytes de los PDFs descargados y pasarlos al scorer y al agente.

- [x] `TEST` `RunPipelineCommandHandler` — verifica que tras `DownloadDocumentsCommand`, los `pdf_texts` extraídos se pasan a `ScoreTenderCommand` (no vacíos)
- [x] `TEST` `RunPipelineCommandHandler` — verifica que los `pdf_paths` reales se pasan a `AnalysisService`
- [x] `IMPL` `RunPipelineCommandHandler` — tras descargar documentos, leer textos PDF con `PdfExtractorPort` y pasarlos a `ScoreTenderCommand` y a `AnalysisService`

### 11.2 RF-06 — Corregir escala de puntuación y umbrales del semáforo (RN-03)

> **Problema**: La escala implementada es 0–70 en vez de 0–100. Los umbrales del semáforo son VERDE≥50/AMARILLO≥25 en lugar de VERDE≥70/AMARILLO≥40 (RN-03).
> **Solución**: Ajustar `_calculate_score()` y `TrafficLight.from_score()` a la especificación real.

- [x] `TEST` `TrafficLight` — VERDE si score ≥ 70, AMARILLO si ≥ 40, ROJO si < 40
- [x] `IMPL` `TrafficLight.from_score()` — actualizar umbrales a ≥70 / ≥40 / <40
- [x] `TEST` `ScoreTenderCommandHandler._calculate_score()` — la puntuación máxima alcanzable es 100 pts
- [x] `IMPL` `ScoreTenderCommandHandler._calculate_score()` — reescalar criterios para que el máximo sea 100

### 11.3 RF-03 — Motor de filtrado: aplicar `sector_keywords` en `matches()`

> **Problema**: `FilterConfig.sector_keywords` existe pero no se usa en `matches()`.

- [x] `TEST` `FilterConfig.matches()` — licitación con keyword en el título pasa el filtro; sin keyword lo supera igualmente (keywords son bonus, no filtro excluyente); licitación con keyword negativo se descarta
- [x] `IMPL` `FilterConfig.matches()` — incorporar `sector_keywords` como filtro de refuerzo o criterio de descarte según si son positivos/negativos

### 11.4 RF-02 — Campos faltantes en `Tender`: CPV, plazo, fecha límite

> **Problema**: Faltan `codi_cpv`, `termini_execucio` y `data_limit_presentacio` en la entidad `Tender` y en la API.

- [ ] `TEST` `Tender` — campos `codi_cpv`, `termini_execucio`, `data_limit_presentacio` opcionales (pueden ser None si la API no los devuelve)
- [ ] `IMPL` `Tender` — añadir campos opcionales `codi_cpv: str | None`, `termini_execucio: str | None`, `data_limit_presentacio: str | None`
- [ ] `IMPL` `TenderModel` + migración Alembic — añadir columnas nullable a la tabla `tenders`
- [ ] `IMPL` `DownloadTendersCommandHandler` — mapear los nuevos campos desde la respuesta de la API (si existen)
- [ ] `IMPL` `tenders.html` — mostrar CPV, plazo y fecha límite en la tabla o en el detalle expandido

### 11.5 RF-04 — Descartar documentos UNKNOWN (RN-02)

> **Problema**: Los documentos `UNKNOWN` se descargan, contradiciendo RN-02.

- [x] `TEST` `DownloadDocumentsCommandHandler` — documentos con `DocumentType.UNKNOWN` no se descargan ni se persisten
- [x] `IMPL` `DownloadDocumentsCommandHandler` — reintroducir el filtro `if doc_type == DocumentType.UNKNOWN: continue` (con test previo que valide el comportamiento)

### 11.7 RF-05 — AnalysisService: corregir pdf_paths y ampliar extracción NLP (RN-02, RF-05)

> **Problema**: El código muerto `for doc in []` en `pipeline_router.py` hace que `pdf_paths` llegue vacío a `AnalysisService`. Además, el `_SYSTEM_PROMPT` no extrae los 5 elementos definidos en RF-05: solvencia, criterios de adjudicación, partidas principales, condiciones especiales y cláusulas atípicas.
> **Solución**: Corregir la recolección de paths y actualizar el prompt.

- [x] `TEST` `pipeline_router` (integración) — tras ejecutar el pipeline, `AnalysisService.analyze()` recibe `pdf_paths` no vacíos cuando hay documentos guardados en disco
- [x] `IMPL` `pipeline_router.py` — eliminar el `for doc in []` y construir `pdf_paths` directamente desde `storage.list_documents()` o desde los bytes guardados
- [x] `IMPL` `AnalysisService._SYSTEM_PROMPT` — ampliar para extraer explícitamente: solvencia, criterios de adjudicación, partidas principales, condiciones especiales y cláusulas atípicas (RF-05)

### 11.6 RF-01 — Paginación completa (todas las páginas, no solo `page=0`)

> **Problema**: `DownloadTendersCommandHandler` solo solicita `page=0`.

- [ ] `TEST` `DownloadTendersCommandHandler` — cuando la API devuelve resultados en página 0, pide también página 1; para cuando una página devuelve lista vacía
- [ ] `IMPL` `DownloadTendersCommandHandler` — iterar páginas hasta recibir lista vacía o alcanzar `max_results`

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

---

## Fase 10 — Persistencia de informes en PostgreSQL

> Actualmente los informes (`ComparativeReport`) y los análisis narrativos se guardan en memoria (`_reports`, `_reports_analysis` en `reports_router.py`). Se pierden al reiniciar el servidor.
> Objetivo: persistirlos en PostgreSQL con CRUD completo.

### 10.1 Dominio — nada que cambiar
> `ComparativeReport` ya existe como entidad. No se modifica.

### 10.2 Modelos SQLAlchemy + migración Alembic

- [ ] `IMPL` `ReportModel` — tabla `reports` con columnas: `id` (UUID PK), `created_at`, `tenders_json` (JSONB o TEXT serializado)
- [ ] `IMPL` `ReportAnalysisModel` — tabla `report_analyses` con columnas: `report_id` (FK → reports.id), `analysis_text` (TEXT)
- [ ] `IMPL` migración Alembic `create_reports_tables`

### 10.3 Aplicación — Port

- [ ] `IMPL` `ReportRepositoryPort` — puerto ABC en `application/ports/` con métodos:
  - `save(report_id: str, report: ComparativeReport) -> None`
  - `save_analysis(report_id: str, text: str) -> None`
  - `get(report_id: str) -> ComparativeReport | None`
  - `get_analysis(report_id: str) -> str | None`
  - `list_all() -> list[tuple[str, ComparativeReport]]`
  - `delete(report_id: str) -> None`

### 10.4 Infraestructura — Repositorio

- [ ] `TEST` `ReportRepository` — integración contra PostgreSQL: save, get, list, delete, save_analysis, get_analysis
- [ ] `IMPL` `ReportRepository` — implementa `ReportRepositoryPort` con SQLAlchemy; serializa `ComparativeReport` a JSON
- [ ] `IMPL` `dependencies.py` — instanciar `ReportRepository` y exponerlo

### 10.5 Aplicación — Router

- [ ] `TEST` `reports_router` — CRUD completo: `GET /reports`, `GET /reports/{id}`, `GET /reports/{id}/analysis`, `DELETE /reports/{id}` usando el repositorio en lugar de los dicts
- [ ] `REFACTOR` `reports_router.py` — sustituir `_reports` y `_reports_analysis` por llamadas a `ReportRepositoryPort`
- [ ] `REFACTOR` `pipeline_router.py` — usar `ReportRepositoryPort.save()` y `save_analysis()` en lugar de acceder a `reports_router._reports`
- [ ] `REFACTOR` `ui_router.py` — usar `ReportRepositoryPort` para las páginas `/reports` y `/reports/{id}`

---

## Fase 12 — Filtrado avanzado (CPV, presupuesto máximo, clasificación, ubicación)

> Mejoras de productividad real: evitar descargar licitaciones fuera del alcance antes incluso de puntarlas.
> Fuente API: `publicacio.dadesPublicacioLot[0].cpvPrincipal.codi`, `llocExecucio.codiNuts`, `solvenciesEconomiques`, `solvenciesTecniques`.

### 12.1 Filtro por CPV

> Usar el código numérico exacto de la actividad para no perder licitaciones con título mal redactado.

- [x] `TEST` `FilterConfig` — nuevo campo `cpv_codes: list[str]` (vacío = sin filtro); `matches()` descarta si `codi_cpv` del tender no está en la lista cuando la lista no está vacía
- [x] `IMPL` `FilterConfig` — añadir `cpv_codes: tuple[str, ...] = field(default_factory=tuple)`
- [ ] `IMPL` `FilterConfigDTO` / `FilterSchema` — exponer `cpv_codes` en API y formulario
- [ ] `IMPL` `filters.html` — campo input para introducir códigos CPV separados por coma
- [ ] `IMPL` `score_tender_command.py` — bonus de puntuación si el CPV coincide con alguno de los configurados

### 12.2 Presupuesto máximo

> Excluir contratos que superen la solvencia económica acreditable.

- [x] `TEST` `FilterConfig` — nuevo campo `max_pressupost: float = 0.0` (0 = sin límite); `matches()` descarta si `pressupost > max_pressupost` cuando `max_pressupost > 0`
- [x] `IMPL` `FilterConfig` — añadir `max_pressupost: float = 0.0`
- [x] `IMPL` `FilterConfigDTO` / `FilterSchema` — exponer `max_pressupost`
- [x] `IMPL` `filters.html` — campo input para presupuesto máximo

### 12.3 Filtro por ubicación (NUTS / provincia)

> En construcción, la distancia reduce el margen. Filtrar por código NUTS o provincia.

- [ ] `TEST` `FilterConfig` — nuevo campo `nuts_codes: list[str]` (vacío = sin filtro); `matches()` descarta si `nuts_code` del tender no está en la lista
- [ ] `IMPL` `Tender` — añadir campo opcional `nuts_code: str | None` (de `llocExecucio.codiNuts`)
- [ ] `IMPL` `TenderModel` + migración Alembic — columna `nuts_code` nullable
- [ ] `IMPL` `DownloadTendersCommandHandler` — mapear `nuts_code` desde `dadesPublicacioLot[0].llocExecucio.codiNuts`
- [ ] `IMPL` `FilterConfig` — añadir `nuts_codes: list[str] = field(default_factory=list)`
- [ ] `IMPL` `FilterConfigDTO` / `FilterSchema` — exponer `nuts_codes`
- [ ] `IMPL` `filters.html` — campo input para códigos NUTS (ej. ES511, ES512)

### 12.4 Filtro por clasificación empresarial (Grupo/Categoría)

> Solo puntuar contratos cuyas exigencias de solvencia puedas acreditar.

- [ ] `TEST` `FilterConfig` — nuevo campo `clasificacion_grupos: list[str]` (vacío = sin filtro); `matches()` descarta si ninguno de los grupos requeridos está en la lista
- [ ] `IMPL` `Tender` — añadir campo `clasificacion_requerida: list[str]` extraído de `solvenciesTecniques[].criteriSolvencia.ca` (texto libre, se parsea best-effort)
- [ ] `IMPL` `DownloadTendersCommandHandler` — mapear `clasificacion_requerida` desde el detalle
- [ ] `IMPL` `FilterConfig` — añadir `clasificacion_grupos: list[str] = field(default_factory=list)`
- [ ] `IMPL` `FilterConfigDTO` / `FilterSchema` — exponer `clasificacion_grupos`
- [ ] `IMPL` `filters.html` — campo input para grupos de clasificación

---

## Fase 13 — Optimización del pipeline (upsert + skip re-processament)

> Evitar re-descarregar documents i re-puntuar licitacions que no han canviat. Important quan el nombre de licitacions creixi.

### 13.1 Upsert de Tender (actualitza si canvia la fase)

- [ ] `TEST` `TenderRepositoryPort` — nou mètode `find_by_expedient_id(expedient_id) -> Tender | None`
- [ ] `IMPL` `TenderRepositoryPort` — afegir mètode abstracte `find_by_expedient_id`
- [ ] `IMPL` `TenderRepository` (PostgreSQL) — implementar `find_by_expedient_id`
- [ ] `IMPL` `DownloadTendersCommandHandler` — si el tender ja existeix i la fase no ha canviat, saltar-se la descàrrega de detall i reutilitzar el pressupost guardat
- [ ] `IMPL` `TenderRepository` — convertir `save()` en upsert (actualitza `fase`, `pressupost`, `data_publicacio` si ja existeix)

### 13.2 Skip de documents ja descarregats

- [ ] `TEST` `DownloadDocumentsCommandHandler` — si el fitxer ja existeix a `storage`, no tornar a descarregar
- [ ] `IMPL` `DocumentStoragePort` — afegir mètode `exists(file_path: str) -> bool`
- [ ] `IMPL` `LocalDocumentStorage` — implementar `exists()`
- [ ] `IMPL` `DownloadDocumentsCommandHandler` — comprovar `storage.exists()` abans de descarregar

---

## Fase 14 — Mejoras UX del Frontend

> Revisión de usabilidad detectada en auditoría de templates. Sin cambios en lógica de dominio ni API.

### 14.1 Indicador de página activa en la navbar (alto impacto)

- [x] `IMPL` `base.html` — marcar el link activo del navbar comparando `request.url.path` con cada ruta; estilo diferenciado (`bg-indigo-800` o subrayado)
- [x] `IMPL` `ui_router.py` — pasar `request` al contexto de todos los templates que usan `base.html`

### 14.2 Fecha de creación en cards de informes (alto impacto)

- [x] `IMPL` `reports.html` — mostrar fecha de creación en cada card de informe
- [x] `IMPL` `report_detail.html` — mostrar fecha en el header del detalle
- [x] `IMPL` `ui_router.py` / `reports_router.py` — exponer `created_at` del informe al template

### 14.3 Reducir columnas en tabla de licitaciones (medio)

- [x] `IMPL` `tenders.html` — fusionar columnas "Docs" y "Accions" en una sola; eliminar click en fila completa (confuso), dejarlo solo en el botón
- [x] `IMPL` `tenders.html` — cambiar emojis semáforo por badges CSS (`<span class="rounded-full ...">`)

### 14.4 Ordenar tabla de informe por puntuación (medio)

- [x] `IMPL` `report_detail.html` — ordenar `report.scored_tenders` por `st.score.total` descendente antes de renderizar
- [x] `IMPL` `ui_router.py` — ordenar la lista antes de pasarla al template

### 14.5 KPIs básicos en el Dashboard (medio)

- [x] `IMPL` `index.html` — añadir sección de stats rápidos: nº tenders en BD, nº informes generados, último pipeline ejecutado
- [x] `IMPL` `ui_router.py` — inyectar esos valores en el contexto del dashboard

### 14.6 Columna Recomanació: tooltip en vez de texto completo (bajo)

- [x] `IMPL` `report_detail.html` — truncar el texto de `recomanacio` en la tabla y mostrar el completo en un `title` tooltip o popover

### 14.7 Menú móvil en navbar (bajo)

- [x] `IMPL` `base.html` — añadir hamburger menu para pantallas pequeñas con HTMX o JS mínimo inline

---

## Fase 15 — Redisseny UX (Dashboard com a pantalla central)

> Reorganització de la interfície perquè un tècnic pugui cercar licitacions, veure resultats i revisar l'anàlisi de Gemini tot en una sola pantalla, sense navegar entre pàgines.
> Cap canvi en lògica de domini ni API — només templates i router de presentació.

### 15.1 Nova navbar: Cerca · Historial · Configuració

- [x] `IMPL` `base.html` — canviar l'ordre i els labels del navbar: `Cerca` (ruta `/`), `Historial` (ruta `/reports`), `Configuració` (ruta `/filters`)
- [x] `IMPL` `base.html` — eliminar l'entrada `Licitacions` del navbar (els resultats es mostren a la pàgina Cerca)

### 15.2 Dashboard com a formulari de cerca

- [x] `IMPL` `index.html` — substituir els KPIs per un formulari de cerca amb els camps: paraules clau, tipus expedient, fase vigent, pressupost mínim, màx. resultats
- [x] `IMPL` `index.html` — el formulari fa un `PUT /api/v1/filters` + `POST /api/v1/pipeline/run` en seqüència via HTMX
- [x] `IMPL` `ui_router.py` — l'endpoint `GET /` passa els valors actuals de `FilterConfig` al template per pre-omplir el formulari

### 15.3 Resultats inline a la pàgina de cerca

- [x] `IMPL` `index.html` — afegir secció de resultats sota el formulari que es carrega via HTMX quan el pipeline acaba
- [x] `IMPL` `index.html` — mostrar l'anàlisi narratiu de Gemini en un desplegable `<details>` just sobre la llista de licitacions
- [x] `IMPL` `index.html` — per cada licitació: fila expandible amb desglose de puntuació + botons de documents
- [x] `IMPL` `partials/search_results.html` — partial nou amb KPIs, Gemini collapsible i taula expandible
- [x] `IMPL` `ui_router.py` — endpoint `GET /partials/search-results` que retorna l'últim informe com a partial

### 15.4 Pàgina Historial (simplificada)

- [x] `IMPL` `reports.html` — conservar tal com està (llista de cercles anteriors amb data, KPIs i enllaç al detall)
- [x] `IMPL` `report_detail.html` — conservar tal com està (informe complet amb anàlisi i taula)

### 15.5 Eliminar pàgina Licitacions independent

- [x] `IMPL` `ui_router.py` — deprecar la ruta `GET /tenders` o redirigir a `/`
- [x] `IMPL` `tenders.html` — pot reutilitzar-se com a partial per als resultats inline o eliminar-se

---

## Fase 16 — Refactor Arquitectura: eliminar accés directe entre routers

> Els routers actuals (`ui_router`, `pipeline_router`) accedeixen al estat intern d'altres routers (`_reports`, `_active_filter`, `_pipeline_status`) violant la regla de dependència de Clean Architecture: "un router mai accedeix al estat intern d'un altre router".
> Objectiu: introduir ports i query handlers perquè la capa de presentació passi per aplicació.

### 16.1 REFACTOR — Port `FilterConfigPort` + `GetActiveFilterQueryHandler`

> Substituir l'accés directe a `filters_router._active_filter` per un port d'aplicació.

- [x] `TEST` `GetActiveFilterQueryHandler` — retorna `FilterConfig | None`; si no n'hi ha cap, retorna `None`
- [x] `IMPL` `FilterConfigPort` — ABC a `application/ports/` amb mètodes: `get() -> FilterConfig | None`, `save(fc: FilterConfig) -> None`
- [x] `IMPL` `InMemoryFilterConfigAdapter` — implementació a `infrastructure/` que guarda el filtre actiu en memòria (substitueix `_active_filter` de `filters_router`)
- [x] `IMPL` `GetActiveFilterQueryHandler` — handler a `application/use_cases/queries/`
- [x] `REFACTOR` `filters_router.py` — usar `FilterConfigPort` en lloc de `_active_filter` global
- [x] `REFACTOR` `ui_router.py` — usar `GetActiveFilterQueryHandler` en lloc de `filters_module._active_filter`
- [x] `REFACTOR` `pipeline_router.py` — usar `GetActiveFilterQueryHandler` en lloc de `filters_module._active_filter`

### 16.2 REFACTOR — Port `PipelineStatusPort` + `GetPipelineStatusQueryHandler`

> Substituir l'accés directe a `pipeline_router._pipeline_status` per un port d'aplicació.

- [x] `TEST` `GetPipelineStatusQueryHandler` — retorna l'estat actual del pipeline (state, total, downloaded, skipped, error)
- [x] `IMPL` `PipelineStatusPort` — ABC a `application/ports/` amb mètodes: `get() -> PipelineStatus`, `update(status: PipelineStatus) -> None`
- [x] `IMPL` `InMemoryPipelineStatusAdapter` — implementació a `infrastructure/` (substitueix `_pipeline_status` de `pipeline_router`)
- [x] `IMPL` `GetPipelineStatusQueryHandler` — handler a `application/use_cases/queries/`
- [x] `REFACTOR` `pipeline_router.py` — usar `PipelineStatusPort` en lloc del global `_pipeline_status`
- [x] `REFACTOR` `ui_router.py` — usar `GetPipelineStatusQueryHandler` en lloc de `pipeline_module._pipeline_status`

### 16.3 REFACTOR — `ReportRepositoryPort` (ja definit a Fase 10, completar aquí si Fase 10 no s'ha fet)

> Substituir l'accés directe a `reports_router._reports` / `_reports_analysis` per `ReportRepositoryPort`.
> **Nota**: Ja cobert a Fase 10.5. Completar aquí si Fase 10 s'implementa abans d'aquest refactor.
