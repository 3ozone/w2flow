# ADR-002: PostgreSQL como base de datos principal

**Estado:** Aceptado  
**Fecha:** 2026-04-23  
**Decisores:** Equipo w2flow

## Contexto

Necesitamos persistir licitaciones descargadas, documentos y puntuaciones. Los requisitos (R-06) fijan PostgreSQL como tecnología obligatoria.

## Decisión

Usamos **PostgreSQL** como única base de datos. Una sola base de datos con tablas por entidad: `tenders`, `documents`, `scores`, `comparative_reports`.

## Alternativas consideradas

| Alternativa | Razón de descarte |
|---|---|
| MariaDB / MySQL | R-06 fija explícitamente PostgreSQL |
| SQLite | Sin concurrencia, no apto para producción |
| MongoDB | Sin ACID, no necesitamos documento-store |
