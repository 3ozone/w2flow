"""Tests unitaris per a ContractacioPublicaClient.

Utilitza unittest.mock per simular les respostes HTTP sense tocar la xarxa.
Verifica el parseo del JSON de l'API → entitats de domini.
"""
from unittest.mock import MagicMock, patch

from app.domain.entities.document import Document
from app.domain.entities.tender import Tender
from app.domain.value_objects.document_type import DocumentType
from app.infrastructure.services.contractacio_publica_client import ContractacioPublicaClient

# ---------------------------------------------------------------------------
# JSON fixtures — respostes simulades de l'API
# ---------------------------------------------------------------------------

_CERCA_AVANCADA_RESPONSE = {
    "content": [
        {
            "expedientId": "f0b5b0e9-474a-482f-b917-908b85d2ca97",
            "id": 300688406,
            "organ": "Ajuntament de Montagut i Oix",
            "titol": "Servei de socorrisme piscina 2026",
        },
        {
            "expedientId": "aaaa-bbbb-cccc-dddd",
            "id": 111222333,
            "organ": "Generalitat de Catalunya",
            "titol": "Obra de pavimentació carrer Major",
        },
    ],
    "totalElements": 2,
    "totalPages": 1,
}

# Fixture — ítem amb ALERTA_FUTURA (sense ANUNCI_LICITACIO → no té documents)
_ITEM_SOLS_ALERTA_FUTURA = {
    "expedientId": "alert-uuid-1111",
    "id": 999001,
    "organ": "Ajuntament de Test",
    "titol": "Licitació futura sense documents",
    "fasesVigents": {
        "ALERTA_FUTURA": {"idPublicacio": 999001},
    },
}

# Fixture — ítem amb ANUNCI_LICITACIO (té documents; idPublicacio propi)
_ITEM_AMB_ANUNCI_LICITACIO = {
    "expedientId": "anunci-uuid-2222",
    "id": 999002,
    "organ": "Generalitat de Catalunya",
    "titol": "Licitació activa amb documents",
    "fasesVigents": {
        "ANUNCI_LICITACIO": {"idPublicacio": 888002},
    },
}

# Fixture — ítem amb ALERTA_FUTURA + ANUNCI_LICITACIO (fases mixtes)
_ITEM_AMB_TOTES_FASES = {
    "expedientId": "mixed-uuid-3333",
    "id": 999003,
    "organ": "Diputació de Barcelona",
    "titol": "Licitació amb múltiples fases",
    "fasesVigents": {
        "ALERTA_FUTURA": {"idPublicacio": 777003},
        "ANUNCI_LICITACIO": {"idPublicacio": 888003},
    },
}

# Fixture — ítem real de l'API amb ANUNCI_EN_TERMINI (faseVigent=30)
# La API retorna 'ANUNCI_EN_TERMINI' en lloc de 'ANUNCI_LICITACIO' per als
# expedients en termini de presentació (descobert via logs 10/05/2026)
_ITEM_AMB_ANUNCI_EN_TERMINI = {
    "expedientId": "termini-uuid-4444",
    "id": 999004,
    "organ": "Generalitat de Catalunya",
    "titol": "Licitació en termini amb documents",
    "fasesVigents": {
        "ANUNCI_EN_TERMINI": {"idPublicacio": 888004},
    },
}

# Fixture — ítem amb ALERTA_FUTURA + ANUNCI_EN_TERMINI (fases mixtes reals)
_ITEM_AMB_ALERTA_I_EN_TERMINI = {
    "expedientId": "mixed-termini-uuid-5555",
    "id": 999005,
    "organ": "Diputació de Girona",
    "titol": "Licitació mixta en termini",
    "fasesVigents": {
        "ALERTA_FUTURA": {"idPublicacio": 777005},
        "ANUNCI_EN_TERMINI": {"idPublicacio": 888005},
    },
}


_DETALL_RESPONSE = {
    "expedientId": "f0b5b0e9-474a-482f-b917-908b85d2ca97",
    "publicacioId": 300688406,
    "fase": "ANUNCI_EN_TERMINI",
    "dades": {
        "versio": 1,
        "codiExpedient": "EXP-2026-001",
        "idExpedient": "f0b5b0e9-474a-482f-b917-908b85d2ca97",
        "publicacio": {
            "id": 300688406,
            "fase": "ANUNCI_EN_TERMINI",
            "expedientId": "f0b5b0e9-474a-482f-b917-908b85d2ca97",
            "teLots": True,
            "dadesBasiquesPublicacio": {
                "codiExpedient": "EXP-2026-001",
                "tipusContracte": {"id": 1},
                "procedimentAdjudicacio": {"id": 2},
            },
            "dadesPublicacio": {
                "pressupostLicitacio": 50000.0,
                "dataTerminiPresentacioOSolicitud": "2026-12-31T23:59:00+01:00",
                "plecsDeClausulesAdministratives": {
                    "ca": [{"id": 101, "titol": "PCAP", "hash": "abc123", "mida": 204800}],
                    "es": [], "en": [], "oc": [],
                },
                "plecsDePrescripcionsTecniques": {
                    "ca": [{"id": 102, "titol": "PPT", "hash": "def456", "mida": 102400}],
                    "es": [], "en": [], "oc": [],
                },
                "memoriaJustificativaContracte": {"ca": [], "es": [], "en": [], "oc": []},
                "annexos": [],
                "altresDocuments": {"ca": [], "es": [], "en": [], "oc": []},
            },
            "dadesPublicacioLot": [
                {
                    "cpvPrincipal": {"codi": "45000000-7"},
                    "duradaTermini": 180,
                    "llocExecucio": {"codiNuts": "ES512"},
                    "classificacionsEmpresarials": [
                        {"grupClassificacioEmpresarial": "C"},
                        {"grupClassificacioEmpresarial": "G"},
                    ],
                }
            ],
            "dadesExpedient": {},
            "publicacionsOficials": [],
            "tipusEsmena": None,
            "motiuEsmena": None,
        },
        "pathPdf": None,
        "pathCertificacio": None,
        "dadesExpedientCpp": None,
        "pathJson": None,
    },
}

_DETALL_SENSE_LOT_RESPONSE = {
    "expedientId": "exp-sense-lot-uuid",
    "publicacioId": 111222333,
    "fase": "ANUNCI_EN_TERMINI",
    "dades": {
        "versio": 1,
        "codiExpedient": None,
        "idExpedient": "exp-sense-lot-uuid",
        "publicacio": {
            "id": 111222333,
            "fase": "ANUNCI_EN_TERMINI",
            "expedientId": "exp-sense-lot-uuid",
            "teLots": False,
            "dadesBasiquesPublicacio": {
                "codiExpedient": None,
                "tipusContracte": None,
                "procedimentAdjudicacio": None,
            },
            "dadesPublicacio": {
                "pressupostLicitacio": None,
                "dataTerminiPresentacioOSolicitud": None,
                "plecsDeClausulesAdministratives": {"ca": [], "es": [], "en": [], "oc": []},
                "plecsDePrescripcionsTecniques": {"ca": [], "es": [], "en": [], "oc": []},
                "memoriaJustificativaContracte": {"ca": [], "es": [], "en": [], "oc": []},
                "annexos": [],
                "altresDocuments": {"ca": [], "es": [], "en": [], "oc": []},
            },
            "dadesPublicacioLot": [],
            "dadesExpedient": {},
            "publicacionsOficials": [],
            "tipusEsmena": None,
            "motiuEsmena": None,
        },
        "pathPdf": None,
        "pathCertificacio": None,
        "dadesExpedientCpp": None,
        "pathJson": None,
    },
}

# Fixture — estructura REAL de l'API (dades.publicacio.dadesPublicacio niuada).
# Reflecteix el JSON real de /detall-publicacio-expedient descobert via logs 10/05/2026.
_DETALL_RESPONSE_NIUADA = {
    "expedientId": "exp-niuat-uuid",
    "publicacioId": 300688406,
    "fase": "ANUNCI_EN_TERMINI",
    "dades": {
        "versio": 1,
        "codiExpedient": "EXP-2026-NIUAT",
        "idExpedient": "exp-niuat-uuid",
        "publicacio": {
            "id": 300688406,
            "fase": "ANUNCI_EN_TERMINI",
            "expedientId": "exp-niuat-uuid",
            "teLots": False,
            "dadesBasiquesPublicacio": {
                "codiExpedient": "EXP-2026-NIUAT",
                "tipusContracte": {"id": 1},
                "procedimentAdjudicacio": {"id": 2},
            },
            "dadesPublicacio": {
                "pressupostLicitacio": 75000.0,
                "dataTerminiPresentacioOSolicitud": "2026-12-31T23:59:00+01:00",
                "plecsDeClausulesAdministratives": {
                    "ca": [{"id": 201, "titol": "PCAP niuat", "hash": "hash201", "mida": 512000}],
                    "es": [], "en": [], "oc": [],
                },
                "plecsDePrescripcionsTecniques": {
                    "ca": [{"id": 202, "titol": "PPT niuat", "hash": "hash202", "mida": 256000}],
                    "es": [], "en": [], "oc": [],
                },
                "memoriaJustificativaContracte": {"ca": [], "es": [], "en": [], "oc": []},
                "annexos": [],
                "altresDocuments": {"ca": [], "es": [], "en": [], "oc": []},
            },
            "dadesPublicacioLot": [],
            "dadesExpedient": {},
            "publicacionsOficials": [],
            "tipusEsmena": None,
            "motiuEsmena": None,
        },
        "pathPdf": None,
        "pathCertificacio": None,
        "dadesExpedientCpp": None,
        "pathJson": None,
    },
}


# Fixture — secció dadesPublicacio retorna un dict en lloc d'una llista.
# Reprodueix el crash real "TypeError: string indices must be integers, not 'str'"
# que passa quan l'API retorna una secció com a objecte (dict) en lloc de llista.
# Iterar un dict Python dóna les seves claus (strings), i raw["id"] peta.
_DETALL_RESPONSE_SECCIO_DICT = {
    "expedientId": "exp-seccio-dict-uuid",
    "publicacioId": 500001,
    "fase": "ANUNCI_EN_TERMINI",
    "dades": {
        "versio": 1,
        "codiExpedient": "EXP-DICT-001",
        "idExpedient": "exp-seccio-dict-uuid",
        "publicacio": {
            "id": 500001,
            "fase": "ANUNCI_EN_TERMINI",
            "expedientId": "exp-seccio-dict-uuid",
            "teLots": False,
            "dadesBasiquesPublicacio": {},
            "dadesPublicacio": {
                "plecsDeClausulesAdministratives": {
                    "ca": [{"id": 301, "titol": "PCAP dict", "hash": "hash301", "mida": 100000}],
                    "es": [], "en": [], "oc": [],
                },
                "plecsDePrescripcionsTecniques": {"ca": [], "es": [], "en": [], "oc": []},
                "memoriaJustificativaContracte": {"ca": [], "es": [], "en": [], "oc": []},
                "annexos": [],
                "altresDocuments": {"ca": [], "es": [], "en": [], "oc": []},
            },
            "dadesPublicacioLot": [],
            "dadesExpedient": {},
            "publicacionsOficials": [],
            "tipusEsmena": None,
            "motiuEsmena": None,
        },
        "pathPdf": None,
        "pathCertificacio": None,
        "dadesExpedientCpp": None,
        "pathJson": None,
    },
}

# Fixture — API retorna seccions com a dict (1 document) en lloc de llista.
# Comportament real observat als logs 10/05/2026: quan hi ha exactament 1 document,
# l'API retorna l'objecte directament (dict) en lloc d'una llista d'1 element.
# plecsDeClausulesAdministratives → dict  (ha de processar-se com [dict])
# plecsDePrescripcionsTecniques   → dict  (ha de processar-se com [dict])
# annexos                         → []    (llista buida, normal)
_DETALL_RESPONSE_SECCIONS_DICT_REAL = {
    "expedientId": "exp-dict-real-uuid",
    "publicacioId": 600001,
    "fase": "ANUNCI_EN_TERMINI",
    "dades": {
        "versio": 1,
        "codiExpedient": "EXP-DICT-REAL-001",
        "idExpedient": "exp-dict-real-uuid",
        "publicacio": {
            "id": 600001,
            "fase": "ANUNCI_EN_TERMINI",
            "expedientId": "exp-dict-real-uuid",
            "teLots": False,
            "dadesBasiquesPublicacio": {},
            "dadesPublicacio": {
                "plecsDeClausulesAdministratives": {
                    "ca": [{"id": 401, "titol": "PCAP real", "hash": "hash401", "mida": 204800}],
                    "es": [], "en": [], "oc": [],
                },
                "plecsDePrescripcionsTecniques": {
                    "ca": [{"id": 402, "titol": "PPT real", "hash": "hash402", "mida": 102400}],
                    "es": [], "en": [], "oc": [],
                },
                "memoriaJustificativaContracte": {"ca": [], "es": [], "en": [], "oc": []},
                "annexos": [],
                "altresDocuments": {"ca": [], "es": [], "en": [], "oc": []},
            },
            "dadesPublicacioLot": [],
            "dadesExpedient": {},
            "publicacionsOficials": [],
            "tipusEsmena": None,
            "motiuEsmena": None,
        },
        "pathPdf": None,
        "pathCertificacio": None,
        "dadesExpedientCpp": None,
        "pathJson": None,
    },
}


# ---------------------------------------------------------------------------
# Helper — crea un client amb Settings mockejades
# ---------------------------------------------------------------------------

def _make_client() -> ContractacioPublicaClient:
    """Crea un ContractacioPublicaClient amb configuració per defecte."""
    return ContractacioPublicaClient(
        base_url="https://contractaciopublica.cat/portal-api",
        timeout=5,
        max_retries=0,
    )


def _mock_response(json_data: object = None, content: bytes = b"", status_code: int = 200) -> MagicMock:
    """Crea un mock de resposta httpx."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.content = content
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# Tests — fetch_tenders
# ---------------------------------------------------------------------------

class TestFetchTenders:
    """Tests per al mètode fetch_tenders."""

    def test_retorna_llista_de_tenders(self):
        """Parseja el camp content[] i retorna una llista de Tender."""
        client = _make_client()
        with patch.object(client, "_get", return_value=_CERCA_AVANCADA_RESPONSE):
            result = client.fetch_tenders(
                {"tipusExpedient": 1, "faseVigent": 0})

        assert len(result) == 2
        assert all(isinstance(t, Tender) for t in result)

    def test_mapeja_camps_obligatoris(self):
        """Mapeja expedientId, id, organ i titol correctament."""
        client = _make_client()
        with patch.object(client, "_get", return_value=_CERCA_AVANCADA_RESPONSE):
            result = client.fetch_tenders({})

        tender = result[0]
        assert tender.expedient_id == "f0b5b0e9-474a-482f-b917-908b85d2ca97"
        assert tender.publicacio_id == 300688406
        assert tender.organ == "Ajuntament de Montagut i Oix"
        assert tender.titol == "Servei de socorrisme piscina 2026"

    def test_retorna_llista_buida_si_content_buit(self):
        """Retorna llista buida si la pàgina no té resultats."""
        client = _make_client()
        with patch.object(client, "_get", return_value={"content": [], "totalElements": 0}):
            result = client.fetch_tenders({})

        assert result == []

    def test_descarta_items_amb_nomes_alerta_futura(self):
        """Ignora ítems que només tenen ALERTA_FUTURA — no tenen documents (RN-15)."""
        client = _make_client()
        response = {
            "content": [_ITEM_SOLS_ALERTA_FUTURA, _ITEM_AMB_ANUNCI_LICITACIO],
            "totalElements": 2,
        }
        with patch.object(client, "_get", return_value=response):
            result = client.fetch_tenders({})

        assert len(result) == 1
        assert result[0].expedient_id == "anunci-uuid-2222"

    def test_usa_idPublicacio_de_anunci_licitacio(self):
        """Usa fasesVigents['ANUNCI_LICITACIO']['idPublicacio'] com a publicacio_id (RN-15)."""
        client = _make_client()
        response = {"content": [_ITEM_AMB_ANUNCI_LICITACIO]}
        with patch.object(client, "_get", return_value=response):
            result = client.fetch_tenders({})

        assert result[0].publicacio_id == 888002

    def test_usa_idPublicacio_de_anunci_licitacio_amb_fases_mixtes(self):
        """Usa ANUNCI_LICITACIO.idPublicacio fins i tot quan ALERTA_FUTURA també hi és."""
        client = _make_client()
        response = {"content": [_ITEM_AMB_TOTES_FASES]}
        with patch.object(client, "_get", return_value=response):
            result = client.fetch_tenders({})

        assert len(result) == 1
        assert result[0].publicacio_id == 888003

    def test_items_sense_fases_vigents_conserven_comportament_original(self):
        """Ítems sense fasesVigents (resposta legacy) usen item['id'] com a publicacio_id."""
        client = _make_client()
        response = {
            "content": [
                {
                    "expedientId": "legacy-uuid",
                    "id": 300688406,
                    "organ": "Organ Test",
                    "titol": "Titol Test",
                }
            ]
        }
        with patch.object(client, "_get", return_value=response):
            result = client.fetch_tenders({})

        assert result[0].publicacio_id == 300688406

    def test_accepta_items_amb_anunci_en_termini(self):
        """Accepta ítems amb ANUNCI_EN_TERMINI (nom real de l'API per faseVigent=30, RN-15)."""
        client = _make_client()
        response = {"content": [_ITEM_AMB_ANUNCI_EN_TERMINI]}
        with patch.object(client, "_get", return_value=response):
            result = client.fetch_tenders({})

        assert len(result) == 1
        assert result[0].expedient_id == "termini-uuid-4444"

    def test_usa_idPublicacio_de_anunci_en_termini(self):
        """Usa fasesVigents['ANUNCI_EN_TERMINI']['idPublicacio'] com a publicacio_id (RN-15)."""
        client = _make_client()
        response = {"content": [_ITEM_AMB_ANUNCI_EN_TERMINI]}
        with patch.object(client, "_get", return_value=response):
            result = client.fetch_tenders({})

        assert result[0].publicacio_id == 888004

    def test_accepta_items_amb_alerta_futura_i_anunci_en_termini(self):
        """Accepta ítems mixtos ALERTA_FUTURA + ANUNCI_EN_TERMINI i usa idPublicacio de ANUNCI_EN_TERMINI."""
        client = _make_client()
        response = {"content": [_ITEM_AMB_ALERTA_I_EN_TERMINI]}
        with patch.object(client, "_get", return_value=response):
            result = client.fetch_tenders({})

        assert len(result) == 1
        assert result[0].publicacio_id == 888005

    def test_descarta_items_amb_nomes_alerta_futura_i_no_altres_fases(self):
        """Descarta ítems que NOMÉS tenen ALERTA_FUTURA, sense cap altra fase activa."""
        client = _make_client()
        response = {
            "content": [_ITEM_SOLS_ALERTA_FUTURA, _ITEM_AMB_ANUNCI_EN_TERMINI],
        }
        with patch.object(client, "_get", return_value=response):
            result = client.fetch_tenders({})

        assert len(result) == 1
        assert result[0].expedient_id == "termini-uuid-4444"


# ---------------------------------------------------------------------------
# Tests — fetch_documents
# ---------------------------------------------------------------------------

class TestFetchDocuments:
    """Tests per al mètode fetch_documents."""

    def test_retorna_documents_de_seccions_conegudes(self):
        """Extreu documents de les seccions PCAP i PPT."""
        client = _make_client()
        with patch.object(client, "_get", return_value=_DETALL_RESPONSE):
            result = client.fetch_documents(
                expedient_id="f0b5b0e9-474a-482f-b917-908b85d2ca97",
                publicacio_id=300688406,
            )

        assert len(result) == 2
        assert all(isinstance(d, Document) for d in result)

    def test_classifica_tipus_document_correctament(self):
        """Assigna DocumentType correcte segons la secció JSON."""
        client = _make_client()
        with patch.object(client, "_get", return_value=_DETALL_RESPONSE):
            result = client.fetch_documents("exp-id", 1)

        tipus = {d.doc_type for d in result}
        assert DocumentType.PCAP in tipus
        assert DocumentType.PPT in tipus

    def test_mapeja_camps_document(self):
        """Mapeja doc_id, titol, hash i mida correctament."""
        client = _make_client()
        with patch.object(client, "_get", return_value=_DETALL_RESPONSE):
            result = client.fetch_documents("exp-id", 1)

        pcap = next(d for d in result if d.doc_type == DocumentType.PCAP)
        assert pcap.doc_id == 101
        assert pcap.titol == "PCAP"
        assert pcap.hash == "abc123"
        assert pcap.mida == 204800

    def test_retorna_llista_buida_si_no_hi_ha_documents(self):
        """Retorna llista buida si totes les seccions estan buides."""
        client = _make_client()
        with patch.object(client, "_get", return_value=_DETALL_SENSE_LOT_RESPONSE):
            result = client.fetch_documents("exp-id", 1)

        assert result == []

    def test_extreu_documents_amb_estructura_dades_publicacio_niuada(self):
        """Extreu documents quan dadesPublicacio és dins de dades.publicacio (estructura real API).

        Test RED — falla amb el bug actual (data.get('dadesPublicacio') busca a l'arrel).
        Ha de passar un cop corregit per usar publicacio.get('dadesPublicacio').
        """
        client = _make_client()
        with patch.object(client, "_get", return_value=_DETALL_RESPONSE_NIUADA):
            result = client.fetch_documents("exp-niuat-uuid", 300688406)

        assert len(result) == 2
        tipus = {d.doc_type for d in result}
        assert DocumentType.PCAP in tipus
        assert DocumentType.PPT in tipus

    def test_camps_document_amb_estructura_niuada(self):
        """Mapeja doc_id, titol, hash i mida correctament amb l'estructura niuada real.

        Test RED — falla amb el bug actual.
        """
        client = _make_client()
        with patch.object(client, "_get", return_value=_DETALL_RESPONSE_NIUADA):
            result = client.fetch_documents("exp-niuat-uuid", 300688406)

        pcap = next(d for d in result if d.doc_type == DocumentType.PCAP)
        assert pcap.doc_id == 201
        assert pcap.titol == "PCAP niuat"
        assert pcap.hash == "hash201"
        assert pcap.mida == 512000

    def test_no_peta_si_seccio_es_dict_en_lloc_de_llista(self):
        """No peta si dadesPublicacio retorna un dict per a una secció (en lloc de llista).

        Comportament esperat: extreure el document del dict de idiomes (clau "ca").
        """
        client = _make_client()
        with patch.object(client, "_get", return_value=_DETALL_RESPONSE_SECCIO_DICT):
            result = client.fetch_documents("exp-seccio-dict-uuid", 500001)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].doc_id == 301

    def test_extreu_documents_quan_seccio_es_dict_un_sol_document(self):
        """Extreu 1 document quan l'API retorna la secció com a dict (no llista).

        Comportament real observat als logs 10/05/2026: quan hi ha exactament
        1 document, l'API retorna l'objecte directament (dict) en lloc de [dict].
        La correcció ha d'envoltar el dict en una llista i processar-lo.
        """
        client = _make_client()
        with patch.object(client, "_get", return_value=_DETALL_RESPONSE_SECCIONS_DICT_REAL):
            result = client.fetch_documents("exp-dict-real-uuid", 600001)

        assert len(result) == 2
        tipus = {d.doc_type for d in result}
        assert DocumentType.PCAP in tipus
        assert DocumentType.PPT in tipus
        pcap = next(d for d in result if d.doc_type == DocumentType.PCAP)
        assert pcap.doc_id == 401
        assert pcap.titol == "PCAP real"


# ---------------------------------------------------------------------------
# Tests — download_document
# ---------------------------------------------------------------------------

class TestDownloadDocument:
    """Tests per al mètode download_document."""

    def test_retorna_bytes_del_pdf(self):
        """Retorna els bytes del PDF descarregat."""
        client = _make_client()
        pdf_bytes = b"%PDF-1.4 fake pdf content"
        with patch.object(client, "_get_bytes", return_value=pdf_bytes):
            result = client.download_document(doc_id=101, hash="abc123")

        assert result == pdf_bytes

    def test_retorna_bytes_buits_si_document_buit(self):
        """Retorna bytes buits si la resposta és buida."""
        client = _make_client()
        with patch.object(client, "_get_bytes", return_value=b""):
            result = client.download_document(doc_id=999, hash="nohash")

        assert result == b""
