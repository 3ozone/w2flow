# Entidades del dominio

## Tender — `Entity` · `Aggregate Root`
Representa una licitación pública publicada en contractaciopublica.cat.

> **Identidad:** `expedientCode` — dos licitaciones son distintas aunque tengan los mismos datos si su código difiere.  
> **Python:** clase normal con `__eq__` basado en `expedientCode`.

| Atributo | Tipo | Descripción |
|---|---|---|
| expedientCode | String | Código único del expediente |
| contractingBody | String | Órgano de contratación |
| amount | float | Importe del contrato |
| cpvCode | String | Código CPV |
| executionDeadline | int | Plazo de ejecución (días) |
| presentationDeadline | DateTime | Fecha límite de presentación |
| publicationDate | DateTime | Fecha de publicación |

**Métodos**

| Método | Retorno | Descripción |
|---|---|---|
| `isExpired()` | bool | True si presentationDeadline < hoy (RN-05) |
| `isNew()` | bool | True si publicationDate == hoy (R-02) |
| `getBasicInfo()` | dict | Devuelve los campos principales como diccionario |

---

## FilterConfig — `Value Object`
Criterios que debe cumplir una licitación para ser candidata (RF-03, RN-01).

> **Sin identidad:** dos `FilterConfig` con los mismos valores son equivalentes.  
> **Python:** `@dataclass(frozen=True)` con `__eq__` por valor.

| Atributo | Tipo | Descripción |
|---|---|---|
| workType | String | Tipología de obra |
| priceRange | Range | Rango de importe (min/max) |
| geographicArea | String | Área geográfica |
| cpvCodes | List | Códigos CPV permitidos |
| executionDeadline | int | Plazo máximo de ejecución |
| businessClassification | String | Clasificación empresarial requerida |

**Métodos**

| Método | Retorno | Descripción |
|---|---|---|
| `validate()` | bool | Comprueba que todos los filtros obligatorios están informados (R-05) |
| `matches(tender)` | bool | True si la licitación cumple todos los criterios configurados (RN-01) |

---

## Document — `Entity`
Fichero adjunto descargado de una licitación candidata (RF-04, RN-02).

> **Identidad:** combinación `tenderId` + `type` — no puede haber dos PCAP del mismo expediente.  
> **Python:** clase normal con `__eq__` basado en `(tenderId, type)`.

| Atributo | Tipo | Descripción |
|---|---|---|
| tenderId | String | Referencia a la licitación |
| type | Enum | PCAP / PPT / TECHNICAL_MEMORY / BUDGET / ANNEXES |
| filePath | String | Ruta de almacenamiento local |
| downloadDate | DateTime | Fecha de descarga |

**Métodos**

| Método | Retorno | Descripción |
|---|---|---|
| `isValidType()` | bool | Comprueba que el tipo está entre los obligatorios: PCAP, PPT, TECHNICAL_MEMORY, BUDGET, ANNEXES (RN-02) |
| `isDuplicate(storage)` | bool | Consulta el almacenamiento para saber si ya fue descargado (RN-06) |

---

## Score — `Value Object`
Resultado de la evaluación de viabilidad de una licitación (RF-06, RN-03).

> **Sin identidad:** inmutable una vez calculado. Si cambian los criterios se crea un `Score` nuevo.  
> **Python:** `@dataclass(frozen=True)` con `__eq__` por valor.

| Atributo | Tipo | Descripción |
|---|---|---|
| tenderId | String | Referencia a la licitación |
| economicScore | float | Puntuación económica (0–100) |
| technicalScore | float | Puntuación técnica (0–100) |
| totalScore | float | Puntuación total (0–100) |
| trafficLight | Enum | GREEN (≥70) / YELLOW (40–69) / RED (<40) |

**Métodos**

| Método | Retorno | Descripción |
|---|---|---|
| `isViable()` | bool | True si totalScore ≥ 40 (semáforo no rojo) |
| `assignTrafficLight()` | Enum | Calcula el semáforo según totalScore (RN-03) |
| `toReport()` | dict | Serializa la puntuación para el informe comparativo (RF-07) |

---

## Requirements — `Value Object`
Información extraída mediante NLP de los documentos de una licitación (RF-05).

> **Sin identidad:** inmutable una vez extraído. Se reemplaza completo si se reprocesa.  
> **Python:** `@dataclass(frozen=True)` con `__eq__` por valor.

| Atributo | Tipo | Descripción |
|---|---|---|
| tenderId | String | Referencia a la licitación |
| solvencyRequirements | List | Requisitos de solvencia económica y técnica |
| technicalRequirements | List | Requisitos técnicos del pliego |
| adminRequirements | List | Condiciones administrativas especiales |
| adjudicationCriteria | List | Criterios de adjudicación y sus pesos |
| specialClauses | List | Cláusulas atípicas detectadas |

**Métodos**

| Método | Retorno | Descripción |
|---|---|---|
| `isEmpty()` | bool | True si no se extrajo ningún requisito (indica fallo de extracción) |
| `toDict()` | dict | Serializa los requisitos para pasarlos al motor de puntuación |

---

## ScoredTender — `Entity`
Agrega todos los datos de una licitación tras pasar por el pipeline completo (RF-06, RF-07).

> **Identidad:** la de su `Tender` interno (`expedientCode`). Es la entidad que "viaja" por el pipeline.  
> **Python:** clase normal con `__eq__` delegado a `tender.expedientCode`.

| Atributo | Tipo | Descripción |
|---|---|---|
| tender | Tender | Licitación original |
| score | Score | Puntuación calculada |
| documents | List[Document] | Documentos descargados |
| requirements | Requirements | Información extraída por NLP |
| evaluationReport | String | Resumen textual de la evaluación |

**Métodos**

| Método | Retorno | Descripción |
|---|---|---|
| `isGo()` | bool | True si score.isViable() — candidata para GO/NO GO (RN-04) |
| `getSummary()` | dict | Devuelve resumen compacto para el informe comparativo |

---

## ComparativeReport — `Entity`
Informe final con todas las licitaciones evaluadas para la decisión GO/NO GO (RF-07).

> **Identidad:** `generationDate` — cada ejecución del proceso genera un informe único.  
> **Python:** clase normal con `__eq__` basado en `generationDate`.

| Atributo | Tipo | Descripción |
|---|---|---|
| scoredTenders | List[ScoredTender] | Lista de licitaciones evaluadas |
| generationDate | DateTime | Fecha y hora de generación |
| summary | String | Resumen ejecutivo del proceso |
| totalProcessed | int | Total de licitaciones procesadas |
| totalViable | int | Total con semáforo verde o amarillo |

**Métodos**

| Método | Retorno | Descripción |
|---|---|---|
| `getViableTenders()` | List[ScoredTender] | Filtra solo las licitaciones viables (no rojas) |
| `generateHTML()` | String | Genera el informe en formato HTML |
| `generateJSON()` | dict | Serializa el informe completo a JSON |
| `summarizeFindings()` | String | Texto resumen para notificación por email (RNF-03) |
