# Releases — w2flow

Historial de releases per fase. Vegeu ADR-008 per a l'estratègia completa.

| Tag | Estat | Contingut |
|---|---|---|
| `v0.1.0` | ✅ inclòs en v1.0.0 | Fase 1 — Domini complet |
| `v0.2.0` | ✅ inclòs en v1.0.0 | Fase 2 — Aplicació completa |
| `v0.3.0` | ✅ inclòs en v1.0.0 | Fase 3 — Infraestructura completa |
| `v0.4.0` | ✅ inclòs en v1.0.0 | Fase 4 — API REST completa |
| `v1.0.0` | ✅ **publicat 2026-05-02** | Fases 1–9 — Producció |

---

## v1.0.0 — 2026-05-02

Primera versió de producció. Inclou totes les fases del projecte:

- **Fase 1–3**: Domini, Aplicació i Infraestructura (entitats, casos d'ús, repositoris PostgreSQL)
- **Fase 4**: API REST completa (tenders, reports, pipeline, filtres)
- **Fase 5–6**: Descàrrega de documents PDF, puntuació i anàlisi amb Gemini
- **Fase 7**: Logging configurable, correcció del filtre UNKNOWN i persistència a disc+DB
- **Fase 8**: Nous endpoints (`DELETE /tenders/{id}`, `DELETE /reports/{id}`, `GET /health`, descàrrega de PDFs per API)
- **Fase 9**: Frontend HTMX + Jinja2 (Dashboard, Licitacions, Informes, Filtres)
