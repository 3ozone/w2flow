# AGENTS.md - Guía de Desarrollo para ikctl

## ⚠️ PROCESO OBLIGATORIO - NUNCA SALTARSE

**REGLA DE ORO**: Cada cambio debe hacerse **UNO POR UNO** con aprobación entre cada paso.

### Flujo Estricto para Cada Tarea

1. **Crear TEST** → ⛔ **PARAR** → Explicar qué test acabas de crear → Pedir permiso para continuar
2. **Crear EXCEPCIÓN** (si necesaria) → ⛔ **PARAR** → Explicar qué excepción creaste → Pedir permiso
3. **Crear IMPLEMENTACIÓN** → ⛔ **PARAR** → Explicar qué implementaste → Pedir permiso
4. **Ejecutar TESTS** → ⛔ **PARAR** → Mostrar resultado (GREEN/RED) → Pedir permiso
5. **Actualizar TASKS.md** → ⛔ **PARAR** → Confirmar cambio → Pedir permiso para siguiente tarea

### ❌ PROHIBIDO

- Hacer múltiples pasos sin aprobación entre ellos
- Crear test + implementación + actualizar TASKS.md en un solo turno
- Usar `multi_replace_string_in_file` para varios archivos diferentes sin aprobación previa
- Continuar a la siguiente tarea sin confirmación explícita del usuario

### 📋 EXCEPCIÓN: Ficheros de planificación

Los ficheros `TASKS.md` (y cualquier fichero de documentación o planificación) **NO se rigen por el flujo estricto de creación de código**. Son guías de trabajo, no código. Se pueden actualizar libremente sin necesidad de test previo ni aprobación paso a paso. Aplica igualmente:

- `docs/v1/*/tasks/TASKS.md`
- `docs/v1/*/requirements.md`
- `docs/v1/*/adrs/*.md`
- `AGENTS.md`
- `README.md`
- `openapi.yaml`

### ✅ Ejemplo CORRECTO

```
Agente: "He creado el test test_password_history.py con 6 tests para validar 
        la entity PasswordHistory. ¿Puedo continuar con la excepción?"
Usuario: "adelante"
Agente: "He añadido InvalidPasswordHistoryError en exceptions.py. 
        ¿Puedo continuar con la implementación de la entity?"
Usuario: "sí"
Agente: "He implementado PasswordHistory en entities.py con validaciones 
        en __post_init__. ¿Ejecuto los tests?"
```

### ❌ Ejemplo INCORRECTO

```
Agente: "He creado el test, la excepción y la entity PasswordHistory. 
        Los tests pasan. ¿Actualizo el TASKS.md?"
```

**RECUERDA**: Un paso a la vez, siempre pedir permiso antes de continuar.

---

## 🧭 Filosofía de Desarrollo

En w2flow seguimos los principios de:

- **Clean Architecture**: Separación estricta en capas (dominio, aplicación, infraestructura, presentación)
- **SOLID**: 5 principios para código mantenible y extensible
- **DRY** (Don't Repeat Yourself): No repetir lógica ni estructuras
- **KISS** (Keep It Simple, Stupid): Soluciones simples, código claro
- **YAGNI** (You Aren't Gonna Need It): Solo implementamos lo necesario
- **TDD** (Test Driven Development): Primero los tests, luego el código

---

## 🌿 Ramas, versiones y releases

### Branching — GitHub Flow

```
main        → siempre estable, nunca commits directos
feature/*   → una rama por tarea del TASKS.md
fix/*       → correcciones puntuales
```

Nomenclatura:
```
feature/domain-tender-entity
feature/application-download-command
fix/score-traffic-light-calculation
```

### Versioning — SemVer

- **PATCH** `1.0.x` — bugfix o ajuste menor
- **MINOR** `1.x.0` — nueva funcionalidad o fase completada
- **MAJOR** `x.0.0` — breaking change en la API

### Tags por fase

| Tag | Contenido |
|---|---|
| `v0.1.0` | Fase 1 — Dominio |
| `v0.2.0` | Fase 2 — Aplicación |
| `v0.3.0` | Fase 3 — Infraestructura |
| `v0.4.0` | Fase 4 — API REST |
| `v1.0.0` | Fase 5 — Producción |

Ver [ADR-008](docs/adrs/008-branching-versioning-strategy.md) para la decisión completa.
