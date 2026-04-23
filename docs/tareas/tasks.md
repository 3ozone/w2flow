# TASKS — w2flow

Backlog ordenado por orden de implementación siguiendo Clean Architecture (dominio primero) y flujo TDD del AGENTS.md.

**Flujo por tarea:** `TEST` → `EXCEPCIÓN` (si aplica) → `IMPL` → `✅ TESTS GREEN`

Leyenda: `[ ]` pendiente · `[x]` completado · `[~]` en progreso

---

## Fase 0 — Setup del proyecto
> Sin TDD — son tareas de configuración

- [ ] Inicializar estructura de carpetas (`domain/`, `application/`, `infrastructure/`, `tests/`)
- [ ] Configurar `pyproject.toml` con dependencias (FastAPI, SQLAlchemy, Pydantic, Alembic, pytest)
- [ ] Configurar variables de entorno (`.env` + `Settings` con Pydantic)
- [ ] Configurar PostgreSQL con Docker Compose
- [ ] Configurar pytest con estructura espejo de `app/`

---

## Fase 1 — Dominio

### 1.1 Enums
> Sin excepciones ni tests complejos — son tipos fijos

- [ ] `TEST` `DocumentType` — valores válidos PCAP, PPT, TECHNICAL_MEMORY, BUDGET, ANNEXES
- [ ] `IMPL` `DocumentType` (Enum)
- [ ] `TEST` `TrafficLight` — valores GREEN, YELLOW, RED y umbrales (≥70, 40-69, <40)
- [ ] `IMPL` `TrafficLight` (Enum)

### 1.2 Value Objects

- [ ] `TEST` `FilterConfig` — validación de campos obligatorios, `matches()` con tender válido e inválido
- [ ] `EXCEPCIÓN` `FilterValidationError`
- [ ] `IMPL` `FilterConfig` (frozen dataclass)

- [ ] `TEST` `Score` — cálculo de `assignTrafficLight()`, `isViable()`, inmutabilidad
- [ ] `IMPL` `Score` (frozen dataclass)

- [ ] `TEST` `Requirements` — `isEmpty()` con y sin datos, `toDict()` estructura correcta
- [ ] `IMPL` `Requirements` (frozen dataclass)

### 1.3 Entidades

- [ ] `TEST` `Tender` — `isExpired()`, `isNew()`, `getBasicInfo()`, igualdad por `expedientCode`
- [ ] `EXCEPCIÓN` `ExpiredTenderError`
- [ ] `IMPL` `Tender` (Entity)

- [ ] `TEST` `Document` — `isValidType()`, identidad por `(tenderId, type)`
- [ ] `EXCEPCIÓN` `DuplicateTenderError`
- [ ] `IMPL` `Document` (Entity)

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


---

## Fase 0 — Setup del proyecto

- [ ] Inicializar estructura de carpetas (`domain/`, `application/`, `infrastructure/`)
- [ ] Configurar `pyproject.toml` / `requirements.txt` con dependencias base (FastAPI, SQLAlchemy, Pydantic, Alembic, pytest)
- [ ] Configurar variables de entorno (`.env` + `Settings` con Pydantic)
- [ ] Configurar PostgreSQL con Docker Compose
- [ ] Configurar pytest con estructura de tests espejo (`tests/domain/`, `tests/application/`, `tests/infrastructure/`)

---

## Fase 1 — Dominio

### Enums / Value Objects simples
- [ ] `DocumentType` (Enum)
- [ ] `TrafficLight` (Enum)
- [ ] `FilterConfig` (Value Object, frozen dataclass)
- [ ] `Score` (Value Object, frozen dataclass)
- [ ] `Requirements` (Value Object, frozen dataclass)

### Entidades
- [ ] `Tender` (Entity)
- [ ] `Document` (Entity)
- [ ] `ScoredTender` (Entity)
- [ ] `ComparativeReport` (Entity)

### Excepciones
- [ ] `DownloadError`
- [ ] `FilterValidationError`
- [ ] `DuplicateTenderError`
- [ ] `ExpiredTenderError`

### Eventos
- [ ] `TenderDownloadedEvent`
- [ ] `EvaluationCompletedEvent`
- [ ] `ProcessFailedEvent`

---

## Fase 2 — Aplicación

### DTOs
- [ ] `FilterConfigDTO`
- [ ] `TenderDTO`
- [ ] `DocumentDTO`
- [ ] `ScoreDTO`

### Ports (interfaces ABC)
- [ ] `LicitationApiPort`
- [ ] `TenderRepositoryPort`
- [ ] `DocumentStoragePort`
- [ ] `NotificationPort`

### Casos de uso — Commands
- [ ] `DownloadTendersCommandHandler`
- [ ] `FilterTendersCommandHandler`
- [ ] `ScoreTenderCommandHandler`

### Casos de uso — Queries
- [ ] `GetScoredTendersQueryHandler`
- [ ] `GetComparativeReportQueryHandler`

---

## Fase 3 — Infraestructura

### Base de datos
- [ ] Modelos SQLAlchemy (`TenderModel`, `DocumentModel`, `ScoreModel`)
- [ ] Migraciones Alembic (creación de tablas)
- [ ] `TenderRepository` (implementa `TenderRepositoryPort`)
- [ ] `DocumentRepository` (implementa `DocumentStoragePort`)

### Cliente externo
- [ ] `ContractacioPublicaClient` (HTTP + paginación)
- [ ] `RetryManager` (backoff exponencial, máx. 2 reintentos)
- [ ] `DownloadMonitor` (progreso y errores)

### Servicios
- [ ] `NlpService` (extracción de requisitos con Timbal)
- [ ] `EmailService` (implementa `NotificationPort`)

---

## Fase 4 — API REST (FastAPI)

### Schemas Pydantic
- [ ] `FilterSchema` (request/response)
- [ ] `TenderSchema`
- [ ] `ReportSchema`
- [ ] `PipelineStatusSchema`

### Routers
- [ ] `pipeline_router` — `POST /pipeline/run`, `GET /pipeline/status`
- [ ] `filters_router` — `GET /filters`, `PUT /filters`
- [ ] `tenders_router` — `GET /tenders`, `GET /tenders/{id}`
- [ ] `reports_router` — `GET /reports`, `GET /reports/{id}`

### App principal
- [ ] `main.py` — setup FastAPI, registro de routers, manejo de errores global

---

## Fase 5 — Tests de integración y ajustes finales

- [ ] Tests de integración del pipeline completo (end-to-end)
- [ ] Validar límite de 1 minuto (R-03)
- [ ] Validar deduplicación (RN-06)
- [ ] Validar descarte de licitaciones expiradas (RN-05)
- [ ] `README.md` con instrucciones de setup y ejecución
