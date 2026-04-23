# ADR-003: FastAPI como framework REST

**Estado:** Aceptado  
**Fecha:** 2026-04-23  
**Decisores:** Equipo w2flow

## Contexto

Necesitamos exponer los endpoints del pipeline, filtros y resultados mediante una API REST en Python.

## Decisión

Usamos **FastAPI** como framework para la capa de presentación REST.

Motivos:
- Validación automática con **Pydantic** (mismo modelo para DTOs y schemas de API)
- Documentación **OpenAPI/Swagger** generada automáticamente
- Soporte nativo **async**, importante para llamadas a la API de contractaciopublica.cat
- Tipado estricto alineado con Clean Architecture

## Alternativas consideradas

| Alternativa | Razón de descarte |
|---|---|
| Flask | Sin validación automática, sin async nativo, más boilerplate |
| Django REST Framework | Demasiado opinionado, acoplado a ORM de Django |
