# ADR-004: Timbal como motor de workflows y agentes

**Estado:** Aceptado  
**Fecha:** 2026-04-23  
**Decisores:** Equipo w2flow

## Contexto

El pipeline (descarga → filtrado → extracción NLP → puntuación → informe) necesita un motor que orqueste pasos secuenciales, gestione contexto entre etapas e integre agentes de IA.

## Decisión

Usamos **Timbal** como framework de workflows y agentes (R-06).

Motivos:
- Conocimiento previo del equipo — curva de aprendizaje mínima
- API más simple y directa que alternativas para workflows lineales
- Integración nativa con agentes de IA para la etapa de extracción NLP
- R-06 lo fija como tecnología obligatoria en esta versión

## Alternativas consideradas

| Alternativa | Razón de descarte |
|---|---|
| LangChain | Mayor complejidad, más abstracciones de las necesarias para este caso (YAGNI) |
| LlamaIndex | Orientado a RAG/búsqueda, no a pipelines de procesamiento batch |
| Prefect / Airflow | Sobre-ingeniería para un pipeline de 1 minuto sin dependencias distribuidas |
