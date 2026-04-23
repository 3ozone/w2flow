# ADR-001: Clean Architecture como patrón estructural

**Estado:** Aceptado  
**Fecha:** 2026-04-23  
**Decisores:** Equipo w2flow

## Contexto

La app combina lógica de negocio compleja (filtrado, puntuación, NLP) con múltiples dependencias externas (API pública, PostgreSQL, email). Necesitamos que el dominio sea testeable de forma aislada y que las dependencias externas sean sustituibles.

## Decisión

Adoptamos **Clean Architecture** con 3 capas:

- `domain/` — entidades, value objects, eventos y excepciones. Sin dependencias externas.
- `application/` — casos de uso (commands/queries), DTOs y ports (interfaces ABC).
- `infrastructure/` — implementaciones concretas: FastAPI, PostgreSQL, clientes HTTP, servicios NLP.

**Regla de dependencia:** las capas internas nunca importan de las externas.

## Alternativas consideradas

| Alternativa | Razón de descarte |
|---|---|
| Arquitectura en capas clásica (MVC) | Mezcla lógica de negocio con framework, dificulta tests unitarios |
| Monolito sin capas | No escala ni es testeable |
