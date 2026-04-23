# ADR-008: Estrategia de ramas, versiones y releases

**Estado:** Aceptado  
**Fecha:** 2026-04-23  
**Decisores:** Equipo w2flow

## Contexto

Necesitamos una estrategia de control de versiones clara para coordinar el desarrollo por fases (según TASKS.md) y mantener `main` siempre estable.

## Decisión

### Branching — GitHub Flow

```
main        → siempre estable y deployable, nunca commits directos
feature/*   → una rama por tarea del TASKS.md
fix/*       → correcciones puntuales
```

Nomenclatura de ramas:
```
feature/domain-tender-entity
feature/application-download-command
feature/infra-postgresql-repository
fix/score-traffic-light-calculation
```

- Cada rama parte de `main` y se mergea mediante PR
- PR requiere tests en verde antes de mergear

### Versioning — SemVer

```
MAJOR.MINOR.PATCH
```

| Tipo | Cuándo | Ejemplo |
|---|---|---|
| PATCH | Bugfix o ajuste menor | `1.0.1` |
| MINOR | Nueva funcionalidad o fase completada | `1.1.0` |
| MAJOR | Breaking change en la API | `2.0.0` |

### Tags y Releases por fase

| Tag | Release | Contenido |
|---|---|---|
| `v0.1.0` | Fase 1 | Dominio completo |
| `v0.2.0` | Fase 2 | Aplicación completa |
| `v0.3.0` | Fase 3 | Infraestructura completa |
| `v0.4.0` | Fase 4 | API REST completa |
| `v1.0.0` | Fase 5 | Validación final — producción |

## Alternativas consideradas

| Alternativa | Razón de descarte |
|---|---|
| Gitflow (develop + release branches) | Sobre-ingeniería para un equipo pequeño (KISS) |
| Trunk-based sin tags | Sin trazabilidad de versiones por fase |
