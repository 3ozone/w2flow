# ADR-007: Fuente de datos única (contractaciopublica.cat)

**Estado:** Aceptado  
**Fecha:** 2026-04-23  
**Decisores:** Equipo w2flow

## Contexto

Existen múltiples plataformas de licitaciones públicas en España (PLACE, perfiles de contratante autonómicos, etc.). Hay que acotar el alcance de la fuente de datos en v1.

## Decisión

La **única fuente de datos** es **contractaciopublica.cat** (R-01).

No se contempla ninguna otra fuente externa en esta versión. El port `LicitationApiPort` abstrae la fuente, lo que permite añadir nuevas fuentes en versiones futuras sin tocar el dominio.

## Alternativas consideradas

| Alternativa | Razón de descarte |
|---|---|
| PLACE (plataforma estatal) | Fuera de alcance v1; la empresa opera en Cataluña |
| Múltiples fuentes agregadas | Complejidad de normalización innecesaria en v1 (YAGNI) |
