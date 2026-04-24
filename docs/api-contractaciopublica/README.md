# API Contractació Pública Catalunya

Guia de referència per a la integració de w2flow amb les APIs de la Plataforma de Serveis de Contractació Pública (PSCP) de Catalunya.

---

## Visió general

Tot passa sota una única URL base:

```
https://contractaciopublica.cat/portal-api
```

| Endpoint | Propòsit |
|---|---|
| `GET /cerca-avancada` | Cercar i llistar licitacions amb filtres |
| `GET /documents-publicacio/json-xifrat/{id}/{token}` | Descarregar el JSON complet d'una fase |
| `GET /descarrega-document/{id}/{token}` | Descarregar document adjunt (PDF, etc.) |

> ⚠️ El fitxer `Manual integració REST_v8.5.pdf` d'aquesta carpeta documenta l'API de **publicació** (per a organismes de contractació que volen publicar al PSCP). **No és la nostra API.** La guia correcta per a w2flow és aquest document.

> ℹ️ L'API de Dades Obertes Catalunya (Socrata) **no és necessària**. El `portal-api` ja disposa d'un endpoint de cerca propi que retorna JSON directament.

---

## API 1 — Cerca avançada (llistat de licitacions)

### Endpoint

```
GET https://contractaciopublica.cat/portal-api/cerca-avancada
```

- **Autenticació**: cap (pública)
- **Content-Type resposta**: `application/json`

### Paràmetres de consulta

| Paràmetre | Tipus | Descripció | Exemple |
|---|---|---|---|
| `page` | int | Pàgina (base 0) | `0` |
| `size` | int | Resultats per pàgina | `20` |
| `tipusExpedient` | int | `1` = Licitacions i contractes | `1` |
| `faseVigent` | int | Fase activa (vegeu valors) | `0` |
| `ambit` | int | Àmbit organitzatiu (vegeu valors) | `1500001` |
| `organ` | int | ID de l'organisme contractant | `17277528` |
| `ambitGeografic` | int | Àmbit geogràfic | `1` |
| `procedimentAdjudicacio` | int | Procediment (vegeu valors) | `401` |
| `tipusContracte` | int | Tipus de contracte (vegeu valors) | `395` |
| `sortField` | text | Camp d'ordenació | `dataUltimaPublicacio` |
| `sortOrder` | text | `asc` / `desc` | `desc` |
| `inclourePub licacionsPlacsp` | bool | Incloure publicacions PLACSP | `false` |

### Valors de `faseVigent`

| Valor | Descripció |
|---|---|
| `0` | Anunci de licitació en termini |
| (altres valors per confirmar amb més captures) | |

### Valors de `ambit`

| Valor | Descripció |
|---|---|
| `1500001` | Departaments i sector públic de la Generalitat de Catalunya |
| `1500002` | Entitats de l'administració local |
| `1500003` | Organismes independents i/o estatutaris |
| `1500004` | Universitats |
| `1500005` | Altres ens |

### Exemple: licitacions obertes avui de la Generalitat

```http
GET https://contractaciopublica.cat/portal-api/cerca-avancada
  ?page=0
  &size=20
  &tipusExpedient=1
  &faseVigent=0
  &ambit=1500001
  &sortField=dataUltimaPublicacio
  &sortOrder=desc
  &inclourePublicacionsPlacsp=false
```

### Paginació

Incrementar `page` fins que la resposta retorni menys resultats que `size`:

```
page=0&size=20  → resultats 1–20
page=1&size=20  → resultats 21–40
...
```

### Estructura de la resposta (confirmada)

Resposta paginada d'estil Spring amb la llista a `content[]`.

```json
{
  "content": [ ... ],
  "pageable": {
    "pageNumber": 0,
    "pageSize": 20,
    "sort": { "unsorted": true, "sorted": false, "empty": true },
    "offset": 0,
    "paged": true,
    "unpaged": false
  },
  "totalPages": 2,
  "totalElements": 34,
  "last": false,
  "numberOfElements": 20,
  "size": 20,
  "number": 0,
  "sort": { "unsorted": true, "sorted": false, "empty": true },
  "first": true,
  "empty": false
}
```

### Estructura de cada element `content[]`

| Camp | Tipus | Nullable | Descripció |
|---|---|---|---|
| `id` | int | no | `publicacioId` — s'usa per descarregar el JSON complet |
| `titol` | string | no | Títol de la licitació |
| `fasesVigents` | object | no | Mapa de fases actives (clau = nom de la fase) |
| `fasesVigents.{fase}.lotsActius` | int | no | Nombre de lots actius en aquesta fase |
| `fasesVigents.{fase}.dataPublicacio` | ISO8601 datetime | no | Data de publicació de la fase |
| `fasesVigents.{fase}.idPublicacio` | int | no | ID de publicació per a la fase (igual que `id` arrel) |
| `esPlacsp` | bool | no | Si és del PLACSP |
| `esAgregatContractes` | bool | sí | Si és un agregat de contractes |
| `esAgregatEncarrecs` | bool | sí | Si és un agregat d'encàrrecs |
| `nomPublicacioAgregada` | string | no | Nom de la publicació (pot coincidir amb `titol`) |
| `descripcio` | string | no | Descripció del contracte |
| `pressupostLicitacio` | float | sí | Pressupost de licitació (null si no informat, `0.0` si informatiu) |
| `pressupostAdjudicacio` | float | sí | Pressupost d'adjudicació (null fins adjudicació) |
| `organ` | string | no | Nom de l'organisme contractant |
| `idOrgan` | int | no | ID de l'organisme contractant |
| `codiExpedient` | string | sí | Codi d'expedient intern de l'organisme (pot ser null) |
| `expedientId` | string (UUID) | no | UUID de l'expedient al PSCP |

### Valors de clau a `fasesVigents`

| Clau | Descripció |
|---|---|
| `ANUNCI_LICITACIO` | Anunci de licitació (termini obert) |
| `ALERTA_FUTURA` | Alerta de futura licitació |
| `AVALUACIO` | Avaluació d'ofertes |
| `ADJUDICACIO` | Adjudicació |
| `FORMALITZACIO` | Formalització |
| `ANULACIO` | Anul·lació |
| `EXECUCIO` | Execució |

> ℹ️ Un item pot tenir diverses fases actives simultàniament si hi ha lots en fases diferents.

> ⚠️ **El token per a `/json-xifrat/` NO apareix en la resposta de `/cerca-avancada`.** Cal capturar de quina crida s'obté (possiblement d'un endpoint de detall de publicació). Vegeu la secció d'API 2 per a l'estat actual d'investigació.

> 📄 Exemple complet de resposta: [`cerca-avancada-response.json`](./cerca-avancada-response.json)

---

## API 2 — JSON detallat per fase

### Endpoint

```
GET https://contractaciopublica.cat/portal-api/documents-publicacio/json-xifrat/{publicacioId}/{encryptedToken}
```

- **`publicacioId`**: identificador numèric de la publicació — és el camp `id` de `/cerca-avancada`
- **`encryptedToken`**: token xifrat únic per publicació — **origen pendent de confirmar** (NO ve de `/cerca-avancada`; probablement d'un endpoint de detall)
- **Autenticació**: cap (token inclòs a la URL)
- **Format resposta**: JSON estructurat (veure models a `docs/api-contractaciopublica/*.json`)

### Com obtenir el `publicacioId`

El `publicacioId` és el camp `id` arrel de cada element de `content[]` a la resposta de `/cerca-avancada`. Per a licitacions en termini (faseVigent=0), la clau activa a `fasesVigents` serà `ANUNCI_LICITACIO`.

### ⚠️ Origen del `encryptedToken` — pendent d'investigació

El token NO apareix a `/cerca-avancada`. Cal fer una captura DevTools addicional a la pàgina de detall d'una licitació per identificar quin endpoint el retorna. Possibles candidats:
- `GET /portal-api/detall-publicacio/{expedientId}/{publicacioId}`
- `GET /portal-api/publicacio/{publicacioId}`

Fins a confirmar, el flux complet de descàrrega no pot implementar-se.

### Exemples de models de resposta

Els fitxers JSON d'aquesta carpeta mostren l'estructura completa de cada fase:

| Fitxer | Fase |
|---|---|
| `anunci-licitacio.json` | Anunci de licitació (principal per a w2flow) |
| `avaluacio.json` | Avaluació d'ofertes |
| `adjudicacio.json` | Adjudicació del contracte |
| `adjudicacio-agregada.json` | Adjudicació agregada |
| `formalitzacio.json` | Formalització del contracte |
| `anulacio.json` | Anul·lació |
| `anunci-previ.json` | Anunci previ |
| `alerta-futura.json` | Alerta futura |
| `consulta-preliminar.json` | Consulta preliminar de mercat |
| `execucio.json` | Fase d'execució |
| `encarrec.json` | Encàrrec a mitjà propi |

---

## API 3 — Descàrrega de documents adjunts (PDF)

### Endpoint

```
GET https://contractaciopublica.cat/portal-api/descarrega-document/{publicacioId}/{token}
```

- Retorna el fitxer adjunt (PDF, ZIP, etc.)
- `Content-Disposition: attachment; filename="Plec de clàusules administratives.pdf"`
- Els IDs i tokens s'obtenen dels links de documents dins el JSON detallat de cada licitació

---

## Flux d'integració de w2flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CERCA DE LICITACIONS                                          │
│    GET /portal-api/cerca-avancada                                │
│    ?tipusExpedient=1&faseVigent=0&page=0&size=20                 │
│    (paginar fins que size > resultats retornats)                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Llista de licitacions + publicacioId (token pendent)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. DESCÀRREGA JSON COMPLET (per cada licitació)                  │
│    GET /portal-api/documents-publicacio/                         │
│        json-xifrat/{publicacioId}/{token}                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ JSON complet amb tots els camps
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. PROCESSAMENT INTERN                                           │
│    - Mapeig a entitats de domini (Tender)                        │
│    - Aplicació de filtres (FilterConfig)                         │
│    - Càlcul de puntuació (ScoreCalculator)                       │
│    - Persistència a PostgreSQL                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Variables d'entorn

```dotenv
PSCP_PORTAL_BASE_URL=https://contractaciopublica.cat/portal-api
LICITATION_API_TIMEOUT=30
LICITATION_API_MAX_RETRIES=2
```

---

## Paginació

```
page=0&size=20  → resultats 1–20
page=1&size=20  → resultats 21–40
...
```

Parar quan la resposta retorni menys resultats que `size`.

---

## Limitacions conegudes

- Els tokens xifrats dels endpoints `/json-xifrat/` i `/descarrega-document/` tenen **vida limitada** — no guardar-los; obtenir-los en fresc a cada execució.
- L'API no requereix autenticació però afegir `User-Agent` a les capçaleres és bona pràctica.
- Els valors numèrics dels paràmetres de filtre (`tipusContracte`, `procedimentAdjudicacio`, etc.) s'han de confirmar fent captures addicionals al DevTools mentre s'utilitzen els filtres del portal.
