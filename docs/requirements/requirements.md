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

1. **RF-01**: Conexión automática a contractaciopublica.cat mediante API REST o web
scraping estructurado, con gestión de autenticación, paginación y reintentos.

2. **RF-02**: Descarga e indexación del listado de licitaciones abiertas con todos los campos
relevantes: código de expediente, órgano de contratación, importe, código CPV, plazo
de ejecución y fecha límite de presentación.

3. **RF-03**: Motor de filtrado configurable por criterios técnicos definidos por el CLIENTE:
tipología de obra, rango de importe, área geográfica, códigos CPV, plazo de ejecución
y clasificación empresarial requerida.

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

2. **RN-02**: El sistema descarga únicamente los documentos definidos como obligatorios: PCAP, PPT, memoria técnica, presupuesto base y anexos. Cualquier otro documento adjunto se ignora.

3. **RN-03**: La puntuación de viabilidad se calcula en una escala de 0 a 100 y determina el semáforo: verde (≥70), amarillo (40–69) y rojo (<40).

4. **RN-04**: La decisión GO/NO GO es responsabilidad exclusiva del Departamento de Estudios; el sistema proporciona el informe comparativo pero no toma la decisión de forma autónoma.

5. **RN-05**: Una licitación con fecha límite de presentación ya vencida en el momento de la descarga se descarta automáticamente, independientemente de su puntuación.

6. **RN-06**: Si una licitación ya fue descargada y evaluada en una ejecución anterior, no se vuelve a procesar para evitar duplicados.

7. **RN-07**: Si se configuran códigos CPV, solo son candidatas las licitaciones cuyo `cpvPrincipal` esté en la lista. Si la lista está vacía, no se aplica filtro CPV.

8. **RN-08**: Si se configura un presupuesto máximo (> 0), se descartan las licitaciones cuyo importe supere ese tope, independientemente de su puntuación.

9. **RN-09**: Si se configuran códigos NUTS, solo son candidatas las licitaciones cuyo lugar de ejecución (`llocExecucio.codiNuts`) coincida con alguno de los códigos configurados. Si la lista está vacía, no se aplica filtro geográfico.

10. **RN-10**: Si se configuran grupos de clasificación empresarial, se descartan las licitaciones que exijan un grupo que no esté en la lista configurada. Si la lista está vacía, no se aplica filtro de clasificación.

## Requisitos de Datos o Integraciones

- Usaremos como lenguaje base python
- Timbal como fremwork para crear agents y workflows
- Como base de datos Postgres
