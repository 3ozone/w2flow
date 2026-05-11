# w2flow

App to create workflows using ai

## Historia de usuario (Como, quiero, para)

Aplicación que descarga las licitaciones desde la web de la administración pública, la descarga se hace aplicando filtros para escoger los decumentos adecuados para la empresa, y una vez se encuentran esos documentos se descargan y se evaluan bajo unos criterios que impone la empresa para saber que licitaciones son aceptables para la empresa.

## Criterios de aceptacion (Dado, cuando, entonces)

- Dado que necesito descargar licitaciones cada dia entonces me conecto automaticamente a la web de contractaciopublica.cat
- Solo debo descargar los documentos nuevos, con fecha de ese mismo dia
- Antes de descargar las licitaciones debo configurar una serie de filtros necesarios para escoger los documentos adecuados
- Una vez descargados todos los documentos debo puntuarlos del 0 al 100 bajo criterios que me da la empresa para saber si se adecuan aun más a las necesidades de la empresa

## Actores

### Empresa

- Propone los filtros y criterios para la aceptación o no de la licitación.

### Api de licitaciones

- Lugar donde podemos bajarnos las documentación, licitaciones y más.

## Requisitos Funcionales

1. **RF-01**: Conexión automática a contractaciopublica.cat mediante API REST pública (sin autenticación), con gestión de paginación y reintentos. El endpoint principal es `GET /portal-api/cerca-avancada`.

2. **RF-02**: Descarga e indexación del listado de licitaciones abiertas con todos los campos
relevantes: código de expediente, órgano de contratación, importe, código CPV, plazo
de ejecución y fecha límite de presentación.

3. **RF-03**: Motor de filtrado configurable por criterios técnicos definidos por el CLIENTE:
tipología de obra, rango de importe, área geográfica, códigos CPV, plazo de ejecución
y clasificación empresarial requerida.

   Los filtros nativos de la API (enviados como parámetros de query) usan los identificadores numéricos propios del endpoint `/cerca-avancada`. Valores por defecto para w2flow:
   - `faseVigent=30` (Anunci de licitació en termini)
   - `tipusContracte=395` (Obres)
   - `procedimentAdjudicacio=401` (Obert)
   - `ambit=1500001` (Generalitat de Catalunya)

   > ⚠️ Los parámetros `sortField=dataUltimaPublicacio` y `sortOrder=desc` son **obligatorios** en cada petición — sin ellos el servidor devuelve HTTP 500.

4. **RF-04**: Descarga automática de la documentación adjunta de las licitaciones
candidatas: pliego de cláusulas administrativas particulares (PCAP), pliego de
prescripciones técnicas (PPT), memoria técnica, presupuesto base y anexos.

5. **RF-05**: Motor de extracción de información (NLP) sobre los documentos descargados:
requisitos de solvencia, criterios de adjudicación, partidas principales, condiciones
especiales y cláusulas atípicas.

6. **RF-06**: Algoritmos de puntuación de viabilidad económica y técnica para cada licitación
candidata, con generación de un informe consolidado (puntuación 0–100 y semáforo
verde/amarillo/rojo).

7. **RF-07**: Panel de comparativa de obras para el Departamento de Estudios, que permite
revisar todas las candidatas y tomar la decisión GO/NO GO de manera
informada.

8. **RF-08**: Filtrado avanzado con cuatro criterios adicionales configurables desde la interfaz:
   - **CPV**: lista de códigos CPV exactos (ej. `45000000-7`); si está configurada, solo pasan licitaciones cuyo `cpvPrincipal` coincida.
   - **Presupuesto máximo**: importe tope que la empresa puede avalar con su solvencia económica; licitaciones por encima se descartan.
   - **Ubicación (NUTS)**: lista de códigos NUTS o provincias (ej. `ES511`, `ES512`); si está configurada, solo pasan licitaciones ejecutadas en esa zona.
   - **Clasificación requerida**: lista de grupos empresariales (ej. `C`, `G`); descarta licitaciones que exijan una clasificación que la empresa no posee.

## Requesitos no funcionales

1. **RNF-01**: Las descargas deben poder monitorizarse para saber si se está descargando los documentos o no.

2. **RNF-02**: En caso de timeout debe poder repertirse la conexión al menos 2 veces, si después de probar 2 veces falla avisar al usuario.

3. **RNF-03**: Se debe avisar una vez se han descargado los documentos y que comieza la comparativa.

4. **RNF-04**: Se debe notificar si hay cualquier error en el proceso.

5. **RNF-05**: El proceso no debe tardar más de 1 minuto.

## Restricciones

1. **R-01**: La fuente de datos es exclusivamente contractaciopublica.cat; no se contempla ninguna otra fuente externa en esta versión.

2. **R-02**: Solo se procesan licitaciones publicadas el mismo día de ejecución del proceso; no se recuperan licitaciones históricas.

3. **R-03**: El proceso completo (descarga + filtrado + puntuación) no debe superar 1 minuto de ejecución.

4. **R-04**: En caso de fallo de conexión, se permiten como máximo 2 reintentos; si persiste el error se interrumpe el proceso y se notifica al usuario.

5. **R-05**: Los filtros de selección deben estar configurados antes de iniciar cualquier descarga; sin filtros activos el proceso no arranca.

6. **R-06**: El lenguaje de implementación es Python, el framework de agentes y workflows es Timbal y la base de datos es PostgreSQL; no se permite cambiar estas tecnologías en la versión actual.

7. **R-07**: Los documentos descargados se almacenan localmente o en la base de datos; no se reenvían a terceros ni se publican externamente.

## Reglas de negocio

1. **RN-01**: Una licitación solo es candidata si supera todos los filtros configurados por la empresa (tipología, importe, área geográfica, CPV, plazo de ejecución y clasificación empresarial).

2. **RN-02**: El sistema descarga únicamente los documentos definidos como obligatorios: PCAP (`plecsDeClausulesAdministratives`), PPT (`plecsDePrescripcionsTecniques`), memoria justificativa (`memoriaJustificativaContracte`) y anexos (`annexos`, `altresDocuments`). Cualquier otro documento adjunto se ignora. Las secciones `BUDGET` (presupuesto base) no tienen clave propia confirmada en la API — se recuperan como `altresDocuments` si existen.

3. **RN-03**: La puntuación de viabilidad se calcula en una escala de 0 a 100 y determina el semáforo: verde (≥70), amarillo (40–69) y rojo (<40).

4. **RN-04**: La decisión GO/NO GO es responsabilidad exclusiva del Departamento de Estudios; el sistema proporciona el informe comparativo pero no toma la decisión de forma autónoma.

5. **RN-05**: Una licitación con fecha límite de presentación ya vencida en el momento de la descarga se descarta automáticamente, independientemente de su puntuación.

6. **RN-06**: Si una licitación ya fue descargada y evaluada en una ejecución anterior, no se vuelve a procesar para evitar duplicados.

7. **RN-07**: Si se configuran códigos CPV, solo son candidatas las licitaciones cuyo `cpvPrincipal` esté en la lista. Si la lista está vacía, no se aplica filtro CPV.

8. **RN-08**: Si se configura un presupuesto máximo (> 0), se descartan las licitaciones cuyo importe supere ese tope, independientemente de su puntuación.

9. **RN-09**: Si se configuran códigos NUTS, solo son candidatas las licitaciones cuyo lugar de ejecución (`llocExecucio.codiNuts`) coincida con alguno de los códigos configurados. Si la lista está vacía, no se aplica filtro geográfico.

10. **RN-10**: Si se configuran grupos de clasificación empresarial, se descartan las licitaciones que exijan un grupo que no esté en la lista configurada. Si la lista está vacía, no se aplica filtro de clasificación.

11. **RN-11**: Si se configura un plazo mínimo o máximo de ejecución (en días), se descartan las licitaciones cuya duración estimada (`duradaTermini`) quede fuera del rango configurado. Si el valor es 0, no se aplica ese extremo del filtro. Si la licitación no tiene duración informada, no se descarta (dato ausente no implica descarte).

12. **RN-12**: La puntuación de viabilidad (0–100) se calcula a partir del análisis NLP del PCAP/PPT según estos criterios:
    - **Solvencia alcanzable** (0–30 pts): los requisitos de solvencia económica y técnica son compatibles con el perfil de la empresa.
    - **Criterios de adjudicación favorables** (0–25 pts): el peso del precio en la adjudicación es ≥ 50% → máximo; < 30% → 0 puntos.
    - **Ausencia de cláusulas atípicas** (0–20 pts): 0 cláusulas → 20 pts; cada cláusula atípica resta 5 pts (mínimo 0).
    - **Procedimiento de acceso** (0–15 pts): procedimiento negociado o restringido → más puntos; abierto sin límite → menos.
    - **Condiciones de ejecución** (0–10 pts): sin condiciones especiales complejas → 10 pts; condiciones sociales/medioambientales exigentes → menos.
    - Total máximo: 100 pts. Semáforo según RN-03: verde ≥ 70, amarillo 40–69, rojo < 40.

13. **RN-13**: El número de licitaciones a procesar por ejecución del pipeline es configurable mediante el campo `max_licitacions` de `FilterConfig`. El valor mínimo es 1 y el máximo es 100. El valor por defecto es 20. Si se configura un valor fuera de ese rango, se rechaza con error de validación (422).

14. **RN-14**: El parámetro `faseVigent` de la API debe tener el valor `30` ("Anunci de licitació en termini" según el sistema de valores propios del endpoint `/cerca-avancada`). El valor `0` corresponde a "Alerta futura" (planes anuales de contratación sin documentos adjuntos). El valor `1000040` del catálogo de Dades Mestres **no funciona** en este endpoint y devuelve HTTP 500. Con `faseVigent=30` el pipeline recibe licitaciones activas con plecs publicados.

15. **RN-15**: Una licitación devuelta por la API cuyo campo `fasesVigents` contenga únicamente la clave `ALERTA_FUTURA` (sin `ANUNCI_LICITACIO`) debe descartarse automáticamente antes de intentar descargar sus documentos. Las alertas futuras son avisos previos sin plecs publicados y no son procesables por el motor NLP.

## Requisitos de Datos o Integraciones

- Usaremos como lenguaje base python
- Timbal como framework para crear agents y workflows
- Como base de datos Postgres

### API contractaciopublica.cat — endpoints utilizados

| Endpoint | Propósito |
|---|---|
| `GET /portal-api/cerca-avancada` | Listado paginado de licitaciones (sin autenticación) |
| `GET /portal-api/detall-publicacio-expedient/{expedientId}/{publicacioId}` | Detalle completo con documentos |
| `GET /portal-api/descarrega-document/{docId}/{hash}` | Descarga de PDF/documento adjunto |

### Catálogo de Dades Mestres (referencia de valores numéricos)

Endpoint público para consultar cualquier tabla de codificación:
```
GET https://gestio.contractaciopublica.cat/api/integracio/codis-dada-mestra?tipusDM={tipusDM}
```

Tablas relevantes para w2flow: `FasesPublicacions`, `TipusContracte`, `ProcedimentAdjudicacio`, `TipusTramitacio`.
