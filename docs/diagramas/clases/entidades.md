# Entidades del dominio

> **Nota de implementación (abril 2026):** Los nombres de atributos siguen los campos reales
> devueltos por la API de contractaciopublica.cat, verificados empíricamente.
> Ver `examples/tender_downloader.py` y `docs/api-contractaciopublica/README.md`.

## Tender — `Entity` · `Aggregate Root`
Representa una licitación pública publicada en contractaciopublica.cat.

> **Identidad:** `expedientId` (UUID string) — dos licitaciones son distintas si su UUID difiere.  
> **Python:** clase normal con `__eq__` basado en `expedientId`.

| Atributo | Tipo | Descripción |
|---|---|---|
| expedientId | String | UUID único del expediente (campo `expedientId` de la API) |
| publicacioId | int | ID de publicación (campo `id` de la API, usado para fetch detail) |
| titol | String | Título de la licitación (campo `titol` de la API) |
| organ | String | Órgano de contratación (campo `organ` de la API) |
| pressupost | float | Importe base de licitación (campo `pressupostLicitacio` de la API) |
| codiExpedient | String | Código legible del expediente (campo `codiExpedient` de la API) |
| fase | String | Fase actual (extraída de `dades.publicacio.fase.text` del detalle) |
| dataPublicacio | String | Fecha de publicación (extraída de `navegacioFases[-1].dataPublicacio`) |

**Métodos**

| Método | Retorno | Descripción |
|---|---|---|
| `isNew()` | bool | True si dataPublicacio == hoy (R-02) |
| `getBasicInfo()` | dict | Devuelve los campos principales como diccionario |

---

## FilterConfig — `Value Object`
Parámetros de búsqueda que se envían a la API (RF-03, R-05).  
El filtrado grueso lo hace la API; `matches()` aplica criterios adicionales sobre los resultados.

> **Sin identidad:** dos `FilterConfig` con los mismos valores son equivalentes.  
> **Python:** `@dataclass(frozen=True)` con `__eq__` por valor.

| Atributo | Tipo | Descripción |
|---|---|---|
| tipusExpedient | int | Tipo de expediente: `1` = licitaciones/contratos |
| faseVigent | int | Fase activa: `0` = solo en plazo (anunci de licitació) |
| maxResults | int | Número máximo de licitaciones a procesar |
| sectorKeywords | List[str] | Palabras clave de sector para filtrado adicional |
| minPressupost | float | Importe mínimo (0 = sin límite) |

**Métodos**

| Método | Retorno | Descripción |
|---|---|---|
| `toApiParams()` | dict | Devuelve los parámetros listos para enviar a `/cerca-avancada` |
| `matches(tender)` | bool | True si la licitación cumple los criterios adicionales de importe y sector (R-05) |

---

## Document — `Entity`
Fichero adjunto descargado de una licitación candidata (RF-04, RN-02).

> **Identidad:** combinación `expedientId` + `docId` — no puede haber dos documentos con el mismo id en el mismo expediente.  
> **Python:** clase normal con `__eq__` basado en `(expedientId, docId)`.

| Atributo | Tipo | Descripción |
|---|---|---|
| expedientId | String | UUID del expediente al que pertenece |
| docId | int | ID del documento (campo `id` del nodo en el JSON de detalle) |
| titol | String | Nombre del fichero (campo `titol` del nodo) |
| hash | String | Hash del fichero para la URL de descarga (campo `hash` del nodo) |
| midaKb | float | Tamaño en KB (campo `mida` / 1024) |
| filePath | String | Ruta local donde se guardó el fichero descargado |
| type | DocumentType | Tipo clasificado a partir del `titol` (PCAP/PPT/TECHNICAL_MEMORY/BUDGET/ANNEXES/UNKNOWN) |

**Métodos**

| Método | Retorno | Descripción |
|---|---|---|
| `isValidType()` | bool | True si `type` != UNKNOWN |
| `isDuplicate(storage)` | bool | Consulta el almacenamiento para saber si ya fue descargado (RN-06) |

---

## DocumentType — `Enum`
Clasificación del tipo de documento adjunto a una licitación.  
Se infiere del campo `titol` del nodo JSON mediante `from_title()`.

| Valor | Descripción |
|---|---|
| `PCAP` | Pliego de Cláusulas Administrativas Particulares |
| `PPT` | Pliego de Prescripciones Técnicas |
| `TECHNICAL_MEMORY` | Memoria técnica |
| `BUDGET` | Presupuesto base |
| `ANNEXES` | Anexos varios |
| `UNKNOWN` | Tipo no reconocido en el `titol` |

**Métodos**

| Método | Retorno | Descripción |
|---|---|---|
| `from_title(titol: str)` | DocumentType | Infiere el tipo a partir del nombre del fichero (heurística por palabras clave) |

---

## Score — `Value Object`
Resultado de la evaluación de viabilidad de una licitación (RF-06, RN-03).

> **Sin identidad:** inmutable una vez calculado. Si cambian los criterios se crea un `Score` nuevo.  
> **Python:** `@dataclass(frozen=True)` con `__eq__` por valor.

| Atributo | Tipo | Descripción |
|---|---|---|
| expedientId | String | UUID del expediente evaluado |
| total | int | Puntuación total (0–70 pts) |
| detall | dict | Desglose por criterio: pressupost, sector_positiu, sector_negatiu, procediment_obert, subcontractació |
| paraulesClauTrobades | List[str] | Palabras clave del sector positivo encontradas |
| penalitzacions | List[str] | Palabras clave del sector negativo encontradas |
| recomanacio | str | "✅ RECOMANADA" (≥50) / "⚠️ A VALORAR" (≥25) / "❌ NO RECOMANADA" (<25) |

**Criterios de puntuación (máx 70 pts)**

| Criterio | Puntos | Condición |
|---|---|---|
| Presupuesto | 25 | ≥ 1.000.000 € |
| | 20 | ≥ 500.000 € |
| | 10 | ≥ 100.000 € |
| | 5 | resto |
| Sector positivo | +5/kw | máx 30 pts |
| Sector negativo | -10/kw | sin límite |
| Procedimiento abierto | +10 | si "procediment obert" en texto |
| Subcontratación | +5 | si "subcontract" en texto |

**Métodos**

| Método | Retorno | Descripción |
|---|---|---|
| `isViable()` | bool | True si total ≥ 25 (semáforo no rojo) |
| `assignTrafficLight()` | TrafficLight | GREEN (≥50) / YELLOW (≥25) / RED (<25) |
| `toReport()` | dict | Serializa la puntuación para el informe comparativo (RF-07) |

---

## Requirements — `Value Object`
Información estructurada extraída por el agente LLM de los documentos de una licitación (RF-05).  
El agente Timbal analiza los PDFs descargados y devuelve esta estructura.

> **Sin identidad:** inmutable una vez extraído. Se reemplaza completo si se reprocesa.  
> **Python:** `@dataclass(frozen=True)` con `__eq__` por valor.

| Atributo | Tipo | Descripción |
|---|---|---|
| expedientId | String | UUID del expediente analizado |
| solvencyRequirements | List[str] | Requisitos de solvencia económica y técnica |
| technicalRequirements | List[str] | Requisitos técnicos del pliego |
| adjudicationCriteria | List[str] | Criterios de adjudicación y sus pesos |
| specialClauses | List[str] | Cláusulas atípicas detectadas |
| rawAgentOutput | String | Texto completo generado por el agente LLM |

**Métodos**

| Método | Retorno | Descripción |
|---|---|---|
| `isEmpty()` | bool | True si no se extrajo ningún requisito (indica fallo del agente) |
| `toDict()` | dict | Serializa los requisitos para el informe comparativo |

---

## ScoredTender — `Entity`
Agrega todos los datos de una licitación tras pasar por el pipeline completo (RF-06, RF-07).

> **Identidad:** la de su `Tender` interno (`expedientId`). Es la entidad que "viaja" por el pipeline.  
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
