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

- [ ] `TEST` `ScoredTender` — `isGo()` delega en `score.isViable()`, `getSummary()` estructura
- [ ] `IMPL` `ScoredTender` (Entity)

- [ ] `TEST` `ComparativeReport` — `getViableTenders()` filtra correctamente, `generateJSON()` estructura
- [ ] `IMPL` `ComparativeReport` (Entity)

### 1.4 Eventos

- [ ] `IMPL` `TenderDownloadedEvent`
- [ ] `IMPL` `EvaluationCompletedEvent`
- [ ] `IMPL` `ProcessFailedEvent`

---

## Fase 2 — Aplicación

### 2.1 DTOs

- [ ] `TEST` `FilterConfigDTO` — conversión desde/hacia `FilterConfig`
- [ ] `IMPL` `FilterConfigDTO`

- [ ] `TEST` `TenderDTO` — conversión desde/hacia `Tender`
- [ ] `IMPL` `TenderDTO`

- [ ] `TEST` `DocumentDTO` — conversión desde/hacia `Document`
- [ ] `IMPL` `DocumentDTO`

- [ ] `TEST` `ScoreDTO` — conversión desde/hacia `Score`
- [ ] `IMPL` `ScoreDTO`

### 2.2 Ports (interfaces ABC)
> Sin tests — son contratos, se testean a través de sus implementaciones

- [ ] `IMPL` `LicitationApiPort`
- [ ] `IMPL` `TenderRepositoryPort`
- [ ] `IMPL` `DocumentStoragePort`
- [ ] `IMPL` `NotificationPort`

### 2.3 Commands

- [ ] `TEST` `DownloadTendersCommandHandler` — mock de `LicitationApiPort`, descarga y filtra por fecha
- [ ] `EXCEPCIÓN` `DownloadError`
- [ ] `IMPL` `DownloadTendersCommandHandler`

- [ ] `TEST` `FilterTendersCommandHandler` — mock de port, aplica `FilterConfig.matches()`
- [ ] `IMPL` `FilterTendersCommandHandler`

- [ ] `TEST` `ScoreTenderCommandHandler` — mock de ports, genera `ScoredTender` con score correcto
- [ ] `IMPL` `ScoreTenderCommandHandler`

### 2.4 Queries

- [ ] `TEST` `GetScoredTendersQueryHandler` — mock de repositorio, devuelve lista paginada
- [ ] `IMPL` `GetScoredTendersQueryHandler`

- [ ] `TEST` `GetComparativeReportQueryHandler` — mock de repositorio, devuelve informe por id
- [ ] `IMPL` `GetComparativeReportQueryHandler`

---

## Fase 3 — Infraestructura

### 3.1 Base de datos

- [ ] `TEST` Modelos SQLAlchemy — mapeo correcto a tablas
- [ ] `IMPL` `TenderModel`, `DocumentModel`, `ScoreModel`
- [ ] `IMPL` Migraciones Alembic (creación de tablas)

- [ ] `TEST` `TenderRepository` — integración contra PostgreSQL (pytest + fixtures)
- [ ] `IMPL` `TenderRepository` (implementa `TenderRepositoryPort`)

- [ ] `TEST` `DocumentRepository` — integración, comprueba deduplicación (RN-06)
- [ ] `IMPL` `DocumentRepository` (implementa `DocumentStoragePort`)

### 3.2 Cliente externo

- [ ] `TEST` `RetryManager` — 2 reintentos, backoff, lanza error al tercer fallo (R-04)
- [ ] `IMPL` `RetryManager`

- [ ] `TEST` `ContractacioPublicaClient` — mock HTTP, paginación, autenticación
- [ ] `IMPL` `ContractacioPublicaClient` (implementa `LicitationApiPort`)

- [ ] `IMPL` `DownloadMonitor` (progreso y registro de errores)

### 3.3 Servicios

- [ ] `TEST` `NlpService` — extracción de requisitos desde documento de prueba
- [ ] `IMPL` `NlpService` (Timbal)

- [ ] `TEST` `EmailService` — mock SMTP, verifica llamada con contenido correcto
- [ ] `IMPL` `EmailService` (implementa `NotificationPort`)

---

## Fase 4 — API REST (FastAPI)

### 4.1 Schemas Pydantic

- [ ] `TEST` `FilterSchema` — validación de campos obligatorios
- [ ] `IMPL` `FilterSchema`, `TenderSchema`, `ReportSchema`, `PipelineStatusSchema`

### 4.2 Routers

- [ ] `TEST` `pipeline_router` — `POST /pipeline/run` lanza command, `GET /pipeline/status` devuelve estado
- [ ] `IMPL` `pipeline_router`

- [ ] `TEST` `filters_router` — `GET` devuelve config activa, `PUT` valida y actualiza
- [ ] `IMPL` `filters_router`

- [ ] `TEST` `tenders_router` — `GET /tenders` lista, `GET /tenders/{id}` detalle y 404
- [ ] `IMPL` `tenders_router`

- [ ] `TEST` `reports_router` — `GET /reports` lista, `GET /reports/{id}` detalle y 404
- [ ] `IMPL` `reports_router`

### 4.3 App principal

- [ ] `IMPL` `main.py` — setup FastAPI, routers, manejo de errores global

---

## Fase 5 — Validación final

- [ ] Test end-to-end del pipeline completo con datos reales
- [ ] Validar tiempo de ejecución < 1 minuto (R-03)
- [ ] Validar deduplicación de licitaciones (RN-06)
- [ ] Validar descarte de licitaciones expiradas (RN-05)
- [ ] `README.md` con instrucciones de setup y ejecución
