# ADR-006: Estrategia de reintentos con máximo 2 intentos y backoff

**Estado:** Aceptado  
**Fecha:** 2026-04-23  
**Decisores:** Equipo w2flow

## Contexto

La conexión a contractaciopublica.cat puede fallar por timeout o error de red. Hay que decidir cuántos reintentos hacer y qué ocurre si se agotan.

## Decisión

Máximo **2 reintentos** con **backoff exponencial** entre intentos (RNF-02, R-04).

- Intento 1 falla → espera y reintenta.
- Intento 2 falla → se interrumpe el proceso y se notifica al usuario via email y log.
- El `RetryManager` encapsula esta lógica en infraestructura; el dominio no sabe nada de reintentos.

## Alternativas consideradas

| Alternativa | Razón de descarte |
|---|---|
| Sin reintentos | No cumple RNF-02 |
| Reintentos ilimitados | Puede exceder el límite de 1 minuto (R-03) |
| Circuit breaker completo | Sobre-ingeniería para 2 reintentos en un proceso batch |
