# w2flow

Pipeline automatizado de descarga, filtrado, puntuación y análisis de licitaciones públicas catalanas (contractaciopublica.cat).

## ¿Qué hace esta aplicación?

Conecta con el portal de contratación pública de la Generalitat de Cataluña, descarga las últimas licitaciones publicadas, las filtra según criterios configurables, las puntúa automáticamente y genera un informe narrativo con IA (Google Gemini vía Timbal) para decidir en qué licitaciones vale la pena presentarse.

**Stack:** Python 3.13 · FastAPI · SQLAlchemy 2.0 · PostgreSQL · Timbal (LLM) · pymupdf · aiosmtplib · Jinja2 · HTMX · TailwindCSS

---

## Requisitos previos

- Python 3.13+
- Docker + Docker Compose
- Clave de API de Google Gemini (`GEMINI_API_KEY`) para el análisis narrativo con IA

---

## Setup inicial

### 1. Clonar e instalar dependencias

```bash
git clone https://github.com/3ozone/w2flow.git
cd w2flow
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Variables de entorno

Crea un fichero `.env` en la raíz del proyecto:

```dotenv
APP_ENV=development
APP_DEBUG=true

# PostgreSQL (coincide con docker-compose.yml)
DATABASE_URL=postgresql+psycopg2://w2flow:w2flow@localhost:5432/w2flow

# API Portal PSCP
PSCP_PORTAL_BASE_URL=https://contractaciopublica.cat/portal-api
LICITATION_API_TIMEOUT=30
LICITATION_API_MAX_RETRIES=2

# Análisis IA — exportar en el mismo shell que uvicorn
GEMINI_API_KEY=your_key_here

# Carpeta donde se guardan los PDFs descargados
DOWNLOAD_DIR=downloads

# Notificaciones SMTP (opcional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=secret
NOTIFICATION_RECIPIENTS=team@example.com
```

> **Importante:** `GEMINI_API_KEY` debe estar exportada en el mismo shell donde arrancas uvicorn, no solo en `.env`. Timbal la lee directamente con `os.getenv()`.
>
> ```bash
> export GEMINI_API_KEY=your_key_here
> uvicorn app.main:app --reload --port 8089
> ```

### 3. Arrancar la base de datos

```bash
docker compose up -d db
```

Adminer (UI web para PostgreSQL) disponible en http://localhost:8081.

### 4. Ejecutar migraciones Alembic

```bash
alembic upgrade head
```

### 5. Arrancar la API

```bash
uvicorn app.main:app --reload --port 8089
```

Swagger UI disponible en http://localhost:8089/docs.

---

## Configuración explicada

### Variables de entorno

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `APP_ENV` | `development` | Entorno de ejecución (`development` / `production`) |
| `APP_DEBUG` | `true` | Activa logs de debug en FastAPI |
| `DATABASE_URL` | _(vacío)_ | URL de conexión a PostgreSQL. Formato: `postgresql+psycopg2://user:pass@host:port/db` |
| `PSCP_PORTAL_BASE_URL` | `https://contractaciopublica.cat/portal-api` | URL base de la API pública. No cambiar en producción |
| `LICITATION_API_TIMEOUT` | `30` | Segundos máximos de espera por respuesta de la API externa |
| `LICITATION_API_MAX_RETRIES` | `2` | Número de reintentos automáticos ante errores de red |
| `GEMINI_API_KEY` | _(vacío)_ | Clave de Google Gemini. Necesaria para el análisis narrativo IA. Sin esta clave el pipeline funciona pero el análisis narrativo falla (no es fatal) |
| `DOWNLOAD_DIR` | `downloads` | Carpeta local donde se guardan los PDFs descargados |
| `SMTP_HOST` | _(vacío)_ | Servidor SMTP para notificaciones por email (opcional) |
| `SMTP_PORT` | `587` | Puerto SMTP |
| `SMTP_USER` | _(vacío)_ | Usuario SMTP |
| `SMTP_PASSWORD` | _(vacío)_ | Contraseña SMTP |
| `NOTIFICATION_RECIPIENTS` | _(vacío)_ | Emails de destino, separados por coma |

### Filtros del pipeline (`PUT /api/v1/filters`)

| Campo | Tipo | Descripción |
|---|---|---|
| `tipus_expedient` | `int` | Tipo de contrato. `1` = licitaciones/contratos. `0` = todos los tipos |
| `fase_vigent` | `int` | Fase activa. `0` = todas las fases (incluye ALERTA_FUTURA). Valores específicos filtran por fase concreta |
| `max_results` | `int` | Máximo de licitaciones a procesar por ejecución (por defecto 20) |
| `sector_keywords` | `list[str]` | Palabras clave de sector positivo para el scoring. Se buscan en el título y en los PDFs |
| `min_pressupost` | `float` | Presupuesto mínimo en euros. `0` = sin límite |

---

## Cómo funciona el pipeline

### Flujo completo

```
contractaciopublica.cat
        │
        ▼
1. DESCARGA ──► Obtiene licitaciones de /cerca-avancada según FilterConfig
        │        Persiste cada una en PostgreSQL (evita duplicados)
        ▼
2. FILTRADO ──► Aplica min_pressupost sobre las licitaciones descargadas
        │
        ▼
3. SCORING ──► Puntúa cada licitación (0–70 pts) y genera GO / NO GO
        │        Persiste ScoredTender en PostgreSQL
        ▼
4. INFORME ──► Agrupa todos los ScoredTenders en un ComparativeReport
        │        Lo guarda en memoria (reports_router) con un UUID
        ▼
5. ANÁLISIS IA ──► Envía el informe a Google Gemini vía Timbal
                    Genera texto narrativo con resumen ejecutivo
                    Lo guarda asociado al report_id
```

### Paso 1 — Descarga de licitaciones

La app llama a `https://contractaciopublica.cat/portal-api/cerca-avancada` con los parámetros del `FilterConfig`. La respuesta es una lista paginada de publicaciones.

Para cada publicación:
- Si no tiene `pressupostLicitacio` en el listado, hace una segunda llamada a `/detall-publicacio-expedient/{expedient_id}/{publicacio_id}` para obtener el detalle.
- Si ya existe en la base de datos (misma combinación `expedient_id` + `publicacio_id`), no la inserta de nuevo pero sí la incluye para scoring.
- Se extraen: título, órgano convocante, presupuesto, fase, fecha de publicación, código de expediente.

### Paso 2 — Filtrado

Se aplica `FilterConfig.matches()` sobre cada licitación. Filtra por `min_pressupost`: si el presupuesto es inferior al mínimo configurado, la licitación se descarta del scoring.

### Paso 3 — Scoring (0–70 puntos)

Cada licitación recibe una puntuación calculada sobre el texto del título y los PDFs descargados:

| Criterio | Puntos | Lógica |
|---|---|---|
| **Presupuesto** | 5–25 pts | `≥ 1.000.000€` → 25 · `≥ 500.000€` → 20 · `≥ 100.000€` → 10 · resto → 5 |
| **Sector positivo** | +5 por keyword (máx. 30) | Palabras del sector: `obres`, `construcció`, `infraestructura`, `reforma`, `rehabilitació`, `urbanisme`, `enginyeria`, `instal·lació`, `manteniment`, `obra civil`, `edificació`, `pavimentació`, `electricitat`, `fontaneria`, `climatització`, etc. |
| **Sector negativo** | −10 por keyword | Penaliza contratos fuera del sector: `software`, `saas`, `plataforma digital`, `aplicació web`, `recursos humans`, `nòmina`, `assegurança`, `servei jurídic`, `auditoria financera`, etc. |
| **Procedimiento abierto** | +10 pts | Si el texto contiene "procediment obert" |
| **Subcontratación** | +5 pts | Si el texto contiene "subcontract" |

**Resultado según puntuación:**

| Puntuación | Semáforo | Recomendación |
|---|---|---|
| ≥ 50 | 🟢 GREEN | RECOMANADA |
| ≥ 25 | 🟡 YELLOW | A VALORAR |
| < 25 | 🔴 RED | NO RECOMANADA |

### Paso 4 — Informe comparativo

Se genera un `ComparativeReport` con todas las licitaciones puntuadas. Se le asigna un `report_id` (UUID) y se guarda en memoria. Es el objeto que devuelve `GET /api/v1/reports`.

### Paso 5 — Análisis narrativo con IA

Se envía el informe a Google Gemini 2.5 Flash vía Timbal con un prompt que pide:
- Formatear cada licitación con todos sus datos
- Ordenarlas por puntuación
- Generar un resumen ejecutivo de las más interesantes para una empresa de ingeniería/construcción

El texto resultante se almacena en memoria asociado al `report_id` y se accede con `GET /api/v1/reports/{id}/analysis`.

> Este paso es **no fatal**: si falla (sin `GEMINI_API_KEY`, timeout, etc.), el pipeline se completa igualmente.

### Dónde se guardan los documentos

Los PDFs adjuntos se descargan en `DOWNLOAD_DIR` (por defecto `downloads/`), organizados por `expedient_id`:

```
downloads/
├── 4636888c-e169-4f13-a199-1dc5cc321873/
│   └── plec_de_condicions.pdf
└── 6ab79f42-584a-4ecc-8427-2162507e6dea/
    └── plec_clausules.pdf
```

El índice de qué archivos corresponden a qué licitación se persiste en PostgreSQL (`DocumentRepository`). Los metadatos sobreviven a reinicios del servidor.

---

## Uso paso a paso

### 1. Configurar filtros

```bash
curl -X PUT http://localhost:8089/api/v1/filters \
  -H "Content-Type: application/json" \
  -d '{
    "tipus_expedient": 1,
    "fase_vigent": 0,
    "max_results": 20,
    "sector_keywords": ["obres", "construcció", "rehabilitació"],
    "min_pressupost": 0
  }'
```

### 2. Lanzar el pipeline

```bash
curl -X POST http://localhost:8089/api/v1/pipeline/run
```

Responde `202 Accepted` inmediatamente. El pipeline se ejecuta en background.

### 3. Consultar el estado

```bash
curl http://localhost:8089/api/v1/pipeline/status
```

Posibles estados: `idle` · `running` · `completed` · `failed`

### 4. Ver las licitaciones puntuadas

```bash
# Todas
curl http://localhost:8089/api/v1/tenders

# Una en concreto
curl http://localhost:8089/api/v1/tenders/4636888c-e169-4f13-a199-1dc5cc321873
```

### 5. Ver los informes y el análisis IA

```bash
# Listar (obtener el id del informe)
curl http://localhost:8089/api/v1/reports

# Detalle del informe
curl http://localhost:8089/api/v1/reports/{report_id}

# Análisis narrativo IA
curl http://localhost:8089/api/v1/reports/{report_id}/analysis

# Eliminar un informe
curl -X DELETE http://localhost:8089/api/v1/reports/{report_id}
```

### 6. Ver documentos de una licitación

```bash
# Listar documentos
curl http://localhost:8089/api/v1/tenders/{id}/documents

# Descargar un PDF
curl -O http://localhost:8089/api/v1/tenders/{id}/documents/{doc_id}/download
```

### 7. Eliminar una licitación

```bash
curl -X DELETE http://localhost:8089/api/v1/tenders/{id}
```

### 8. Health check

```bash
curl http://localhost:8089/api/v1/health
```

---

## Interfaz web

Además de la API REST, la aplicación incluye una interfaz web completa accesible en http://localhost:8089.

| URL | Descripción |
|-----|-------------|
| `/` | Dashboard — filtro activo, botón de pipeline, estado en tiempo real |
| `/tenders` | Tabla de licitaciones con semáforo 🟢🟡🔴 y documentos expandibles |
| `/reports` | Lista de informes comparativos generados |
| `/reports/{id}` | Detalle del informe + análisis narrativo de Gemini |
| `/filters` | Formulario para configurar los filtros del pipeline |

La UI utiliza **HTMX** para actualizaciones parciales sin recargar la página y **TailwindCSS** para el estilo. El estado del pipeline se actualiza automáticamente cada 2 segundos mientras está en ejecución.

---

## Endpoints disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/v1/filters` | Obtiene la configuración de filtros activa |
| `PUT` | `/api/v1/filters` | Actualiza los filtros antes de lanzar el pipeline |
| `POST` | `/api/v1/pipeline/run` | Lanza el pipeline completo (202 Accepted, background) |
| `GET` | `/api/v1/pipeline/status` | Estado del proceso: idle / running / completed / failed |
| `GET` | `/api/v1/tenders` | Lista todas las licitaciones puntuadas |
| `GET` | `/api/v1/tenders/{id}` | Detalle de una licitación con su score |
| `GET` | `/api/v1/tenders/{id}/documents` | Lista los documentos (PDFs) de una licitación |
| `GET` | `/api/v1/tenders/{id}/documents/{doc_id}/download` | Descarga un PDF |
| `DELETE` | `/api/v1/tenders/{id}` | Elimina una licitación y sus documentos/scores en cascada |
| `GET` | `/api/v1/reports` | Lista los informes comparativos generados |
| `GET` | `/api/v1/reports/{id}` | Detalle de un informe con todas las licitaciones |
| `GET` | `/api/v1/reports/{id}/analysis` | Análisis narrativo IA del informe (texto de Gemini) |
| `DELETE` | `/api/v1/reports/{id}` | Elimina un informe |
| `GET` | `/api/v1/health` | Health check: estado general y de la base de datos |

Documentación interactiva completa (Swagger UI): http://localhost:8089/docs

---

## Tests

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=app --cov-report=term-missing

# Solo tests unitarios (sin DB)
pytest tests/domain tests/application

# Tests end-to-end (sin DB ni HTTP real)
pytest tests/test_e2e_pipeline.py -v
```

---

## Estructura del proyecto

```
app/
├── domain/          # Entidades, value objects, excepciones (sin dependencias externas)
├── application/     # Commands, queries, ports (interfaces ABC)
├── infrastructure/  # Repositorios SQLAlchemy, clientes HTTP, servicios
│   └── api/v1/      # Routers FastAPI + schemas Pydantic
└── main.py          # Entry point FastAPI
tests/               # Espejo de app/ + tests e2e
docs/                # ADRs, diagramas, requisitos, tareas
examples/            # Scripts de ejemplo (tender_downloader.py, timbal_workflow.py)
```

---

## Arquitectura

Sigue **Clean Architecture** con separación estricta en capas (dominio → aplicación → infraestructura → presentación). Ver [docs/arquitectura/architecture.md](docs/arquitectura/architecture.md) y los [ADRs](docs/adrs/) para las decisiones de diseño.

