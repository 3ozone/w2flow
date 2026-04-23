# ADR-005: Pipeline batch diario como estrategia de ejecución

**Estado:** Aceptado  
**Fecha:** 2026-04-23  
**Decisores:** Equipo w2flow

## Contexto

Las licitaciones se publican diariamente en contractaciopublica.cat. Hay que decidir si el sistema procesa en tiempo real (event-driven) o en batch.

## Decisión

Usamos un **pipeline batch de ejecución diaria bajo demanda** (disparado vía `POST /api/v1/pipeline/run`).

- Solo se procesan licitaciones publicadas **el mismo día** de ejecución (R-02).
- No se recuperan ni procesan licitaciones históricas.
- El proceso completo debe finalizar en **menos de 1 minuto** (R-03).

## Alternativas consideradas

| Alternativa | Razón de descarte |
|---|---|
| Event-driven (webhooks) | contractaciopublica.cat no ofrece webhooks |
| Cron automático interno | Añade complejidad de scheduling; el usuario prefiere control manual en v1 |
| Procesamiento incremental continuo | YAGNI — volumen diario no lo justifica |
