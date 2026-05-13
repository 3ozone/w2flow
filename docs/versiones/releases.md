# Releases — w2flow

Historial de releases per fase. Vegeu ADR-008 per a l'estratègia completa.

| Tag | Estat | Contingut |
|---|---|---|
| `v0.1.0` | ✅ inclòs en v1.0.0 | Fase 1 — Domini complet |
| `v0.2.0` | ✅ inclòs en v1.0.0 | Fase 2 — Aplicació completa |
| `v0.3.0` | ✅ inclòs en v1.0.0 | Fase 3 — Infraestructura completa |
| `v0.4.0` | ✅ inclòs en v1.0.0 | Fase 4 — API REST completa |
| `v1.0.0` | ✅ **publicat 2026-05-02** | Fases 1–9 — Producció |
| `v2.0.0` | ⏳ **pendent de release** | Fases E–J + bugfixes — Documents, LLM config-driven, UI completa |

---

## v2.0.0 — pendent

Documents adjunts, comentaris LLM, LLM config-driven i UI completa llegint de BD.

### Fases E–F — Correccions paràmetres API
- `FilterConfig` valors per defecte corregits: `fase_vigent=30`, `ambit=1500001`, `tipus_contracte=395`, `procediment_adjudicacio=401`
- `ContractacioPublicaClient` descarta ítems `ALERTA_FUTURA` (RN-15)
- `publicacio_id` obtingut de `fasesVigents.ANUNCI_LICITACIO.idPublicacio`

### Fase G — LLM config-driven
- Model LLM configurable via `.env` (`LLM_MODEL`, `LLM_API_KEY`) sense canviar codi
- `TimbalNlpAnalyser` suporta qualsevol proveïdor LiteLLM; providers PDF-natiu (`google`, `anthropic`) vs text via `pymupdf` (truncat a 32k chars)

### Fase H — Millores pipeline
- Desglose de puntuació per 5 criteris (RN-12) en `ScoredTenderDTO.detall`
- `FetchCandidatesUseCase` amb paginació automàtica: `page = count() // max_licitacions`
- Nou mètode `count()` a `TenderRepositoryPort` i `SqlAlchemyTenderRepository`

### Fase J — Documents adjunts, comentaris LLM i persistència completa
- Noves entitats de domini: `TenderDocument`, `DocumentAnalysis` (amb `comentaris_per_doc`, `recomendacio`)
- Nova taula `tender_documents` + noves columnes a `tenders` (migració Alembic)
- Port `DocumentStoragePort` + `LocalFileDocumentStorage` (PDFs a `downloads/<id>/`)
- Port `TenderDocumentRepositoryPort` + `SqlAlchemyTenderDocumentRepository`
- `RunPipelineUseCase` actualitzat: save+flush → disc → BD docs → NLP → `update_score()` → `db.commit()`
- Nous endpoints: `GET /api/v1/documents/{id}/{filename}/download`, `DELETE /api/v1/documents/{id}/{filename}`
- `/licitacions` llegeix de BD (no de `_last_report`): layout expandible, desglose criteris, docs + comentaris LLM, recomanació GO/NO GO
- Dashboard simplificat: botó "Veure licitacions →" en completar pipeline

### Bugfixes
- `SqlAlchemyTenderRepository.save()` — `session.flush()` per satisfer FK `tender_documents → tenders`
- `_run_pipeline_task()` — `db.commit()` + `db.rollback()` (sense commit tot es feia rollback en tancar)
- `SqlAlchemyTenderRepository.list_all()` — mètode restaurat (havia quedat fusionat dins `save()`)

---

## v1.0.0 — 2026-05-02

Primera versió de producció. Inclou totes les fases del projecte:

- **Fase 1–3**: Domini, Aplicació i Infraestructura (entitats, casos d'ús, repositoris PostgreSQL)
- **Fase 4**: API REST completa (tenders, reports, pipeline, filtres)
- **Fase 5–6**: Descàrrega de documents PDF, puntuació i anàlisi amb Gemini
- **Fase 7**: Logging configurable, correcció del filtre UNKNOWN i persistència a disc+DB
- **Fase 8**: Nous endpoints (`DELETE /tenders/{id}`, `DELETE /reports/{id}`, `GET /health`, descàrrega de PDFs per API)
- **Fase 9**: Frontend HTMX + Jinja2 (Dashboard, Licitacions, Informes, Filtres)
