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

## 🔧 Proceso Obligatorio para Refactors

Un refactor es cualquier cambio que **modifica la estructura del código sin añadir funcionalidad nueva** (mover responsabilidades entre capas, extraer un handler, introducir un puerto, renombrar, etc.).

**REGLA DE ORO**: Los refactors siguen el mismo flujo estricto que las nuevas tareas — **un paso a la vez, con aprobación entre cada paso**.

### Flujo Estricto para Refactors

1. **Crear TEST** que cubra el comportamiento actual (si no existe) → ⛔ **PARAR** → Explicar qué test acabas de crear → Pedir permiso para continuar
2. **Crear EXCEPCIÓN** (si necesaria) → ⛔ **PARAR** → Explicar qué excepción creaste → Pedir permiso
3. **Crear IMPLEMENTACIÓN** del código refactorizado → ⛔ **PARAR** → Explicar qué cambiaste y por qué respeta la arquitectura → Pedir permiso
4. **Ejecutar TESTS** → ⛔ **PARAR** → Mostrar resultado (GREEN/RED) → Pedir permiso
5. **Actualizar TASKS.md** → ⛔ **PARAR** → Confirmar cambio → Pedir permiso para el siguiente paso del refactor

### ❌ PROHIBIDO en Refactors

- Mover código a otra capa sin test previo que valide el comportamiento
- Refactorizar varios ficheros a la vez sin aprobación entre cada uno
- Aprovechar un refactor para añadir funcionalidad nueva ("refactor" ≠ "refactor + feature")
- Cambiar la firma pública de un handler o port sin actualizar todos sus usos en el mismo paso

### 🏛️ Reglas de Arquitectura para Refactors

- **Siempre respetar la regla de dependencia**: dominio → aplicación → infraestructura → presentación. Nunca al revés.
- **Presentación nunca instancia entidades de dominio** directamente — debe pasar por un handler de aplicación.
- **Un router nunca accede al estado interno de otro router** — si necesita compartir datos, usar un port o servicio de aplicación.
- **Los ports (ABC) se definen en aplicación** antes de que exista la implementación en infraestructura.
- Ante la duda: si el código de test quedaría igual antes y después del refactor, el refactor respeta el contrato.

### ✅ Ejemplo CORRECTO de Refactor

```
Agente: "He creado test_run_pipeline_command.py con 3 tests que validan el
        comportamiento actual del pipeline (download→filter→score→report).
        ¿Puedo continuar con el RunPipelineCommandHandler?"
Usuario: "adelante"
Agente: "He creado RunPipelineCommandHandler en application/use_cases/commands/.
        Orquesta las 4 etapas y devuelve ComparativeReport — sin tocar presentación.
        ¿Puedo actualizar pipeline_router.py para que lo use?"
Usuario: "sí"
Agente: "He actualizado pipeline_router.py: ya no importa ComparativeReport del
        dominio ni accede a reports_router._reports directamente.
        ¿Ejecuto los tests?"
```

### ❌ Ejemplo INCORRECTO de Refactor

```
Agente: "He refactorizado pipeline_router.py moviendo la lógica a
        RunPipelineCommandHandler y también he añadido fetch_documents
        al pipeline de paso. Los tests pasan. ¿Actualizo TASKS.md?"
```

**RECUERDA**: Refactor = solo mover/reorganizar. Un paso a la vez. Sin features nuevas de regalo.

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
