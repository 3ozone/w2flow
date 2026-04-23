# Convenciones de nombres — Clean Architecture en Python

## Estructura de carpetas

```
app/
├── domain/
│   ├── entities/
│   ├── value_objects/
│   ├── events/
│   └── exceptions/
├── application/
│   ├── dtos/
│   ├── ports/
│   └── use_cases/
│       ├── commands/
│       └── queries/
└── infrastructure/
    ├── api/
    ├── repositories/
    └── services/
```

---

## Reglas generales Python

| Elemento | Convención | Ejemplo |
|---|---|---|
| Módulos / ficheros | `snake_case` | `tender_repository.py` |
| Clases | `PascalCase` | `TenderRepository` |
| Métodos y funciones | `snake_case` | `get_tender_by_id()` |
| Variables y parámetros | `snake_case` | `tender_list` |
| Constantes | `UPPER_SNAKE_CASE` | `MAX_RETRIES = 2` |
| Atributos privados | `_snake_case` | `_base_url` |
| Interfaces / Puertos (ABC) | `PascalCase` + sufijo `Port` o `Repository` | `TenderRepositoryPort` |

---

## Capa de Dominio (`domain/`)

### Entidades
- Fichero: `<entidad>.py` → `tender.py`
- Clase: `PascalCase` → `Tender`
- Sin dependencias externas

```
domain/entities/tender.py          → class Tender
domain/entities/document.py        → class Document
domain/entities/score.py           → class Score
domain/entities/filter_config.py   → class FilterConfig
```

### Value Objects
- Fichero: `<nombre>.py` → `price_range.py`
- Clase: `PascalCase` → `PriceRange`
- Inmutables (`@dataclass(frozen=True)`)

```
domain/value_objects/price_range.py     → class PriceRange
domain/value_objects/traffic_light.py   → class TrafficLight (Enum)
domain/value_objects/cpv_code.py        → class CpvCode
domain/value_objects/document_type.py  → class DocumentType (Enum)
```

### Eventos
- Fichero: `<nombre>_event.py` → `tender_downloaded_event.py`
- Clase: `PascalCase` + sufijo `Event` → `TenderDownloadedEvent`

```
domain/events/tender_downloaded_event.py    → class TenderDownloadedEvent
domain/events/evaluation_completed_event.py → class EvaluationCompletedEvent
domain/events/process_failed_event.py       → class ProcessFailedEvent
```

### Excepciones
- Fichero: `<nombre>_error.py` → `download_error.py`
- Clase: `PascalCase` + sufijo `Error` → `DownloadError`

```
domain/exceptions/download_error.py         → class DownloadError
domain/exceptions/filter_validation_error.py → class FilterValidationError
domain/exceptions/duplicate_tender_error.py  → class DuplicateTenderError
domain/exceptions/expired_tender_error.py    → class ExpiredTenderError
```

---

## Capa de Aplicación (`application/`)

### DTOs
- Fichero: `<nombre>_dto.py` → `tender_dto.py`
- Clase: `PascalCase` + sufijo `DTO` → `TenderDTO`
- Inmutables (`@dataclass(frozen=True)`)

```
application/dtos/tender_dto.py        → class TenderDTO
application/dtos/score_dto.py         → class ScoreDTO
application/dtos/filter_config_dto.py → class FilterConfigDTO
application/dtos/document_dto.py      → class DocumentDTO
```

### Puertos / Interfaces
- Fichero: `<nombre>_port.py` → `tender_repository_port.py`
- Clase: ABC con sufijo `Port` (servicios externos) o `Repository` (persistencia)

```
application/ports/tender_repository_port.py    → class TenderRepositoryPort(ABC)
application/ports/document_storage_port.py     → class DocumentStoragePort(ABC)
application/ports/notification_port.py         → class NotificationPort(ABC)
application/ports/licitation_api_port.py       → class LicitationApiPort(ABC)
```

### Casos de Uso — Commands (modifican estado)
- Fichero: `<accion>_<entidad>_command.py` → `download_tenders_command.py`
- Clase handler: `PascalCase` + sufijo `CommandHandler`
- Clase command (input): `PascalCase` + sufijo `Command`

```
application/use_cases/commands/download_tenders_command.py
    → class DownloadTendersCommand
    → class DownloadTendersCommandHandler

application/use_cases/commands/score_tender_command.py
    → class ScoreTenderCommand
    → class ScoreTenderCommandHandler

application/use_cases/commands/filter_tenders_command.py
    → class FilterTendersCommand
    → class FilterTendersCommandHandler
```

### Casos de Uso — Queries (solo lectura)
- Fichero: `<accion>_<entidad>_query.py` → `get_scored_tenders_query.py`
- Clase handler: `PascalCase` + sufijo `QueryHandler`
- Clase query (input): `PascalCase` + sufijo `Query`

```
application/use_cases/queries/get_scored_tenders_query.py
    → class GetScoredTendersQuery
    → class GetScoredTendersQueryHandler

application/use_cases/queries/get_comparative_report_query.py
    → class GetComparativeReportQuery
    → class GetComparativeReportQueryHandler
```

---

## Capa de Infraestructura (`infrastructure/`)

### Repositorios (implementan puertos)
- Fichero: `<entidad>_repository.py` → `tender_repository.py`
- Clase: `PascalCase` + sufijo `Repository`

```
infrastructure/repositories/tender_repository.py    → class TenderRepository(TenderRepositoryPort)
infrastructure/repositories/document_repository.py  → class DocumentRepository(DocumentStoragePort)
```

### Servicios externos (implementan puertos)
- Fichero: `<nombre>_service.py` → `licitation_api_service.py`
- Clase: `PascalCase` + sufijo `Service`

```
infrastructure/services/licitation_api_service.py  → class LicitationApiService(LicitationApiPort)
infrastructure/services/email_service.py            → class EmailService(NotificationPort)
infrastructure/services/nlp_service.py              → class NlpService
```

### API / Adaptadores
- Fichero: `<nombre>_client.py` → `contractacio_publica_client.py`
- Clase: `PascalCase` + sufijo `Client`

```
infrastructure/api/contractacio_publica_client.py → class ContractacioPublicaClient
```

---

## Resumen rápido de sufijos

| Sufijo | Capa | Propósito |
|---|---|---|
| *(sin sufijo)* | Domain | Entidad de dominio |
| `Event` | Domain | Evento de dominio |
| `Error` | Domain | Excepción de dominio |
| `DTO` | Application | Objeto de transferencia de datos |
| `Port` | Application | Interfaz de servicio externo (ABC) |
| `Repository` | Application / Infra | Interfaz o impl. de persistencia |
| `Command` / `CommandHandler` | Application | Caso de uso que modifica estado |
| `Query` / `QueryHandler` | Application | Caso de uso de solo lectura |
| `Service` | Infrastructure | Implementación de servicio externo |
| `Client` | Infrastructure | Cliente HTTP / API |
