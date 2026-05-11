"""Implementació HTTP del port TenderApiPort per a contractaciopublica.cat (RF-01, RF-02, RF-04)."""
from app.domain.value_objects.document_type import DocumentType
from app.domain.entities.tender import Tender
from app.domain.entities.document import Document
from app.application.ports.tender_api_port import TenderApiPort
from app.application.exceptions.application_errors import TenderApiError
import logging

import httpx

logger = logging.getLogger(__name__)


_DOCUMENT_SECTIONS = [
    "plecsDeClausulesAdministratives",
    "plecsDePrescripcionsTecniques",
    "memoriaJustificativaContracte",
    "annexos",
    "altresDocuments",
]


class ContractacioPublicaClient(TenderApiPort):
    """Client HTTP síncron per a l'API de contractaciopublica.cat.

    Implementa TenderApiPort fent crides a:
      - GET /cerca-avancada          → llista paginada de licitacions
      - GET /detall-publicacio-expedient/{exp_id}/{pub_id} → detall complet
      - GET /descarrega-document/{doc_id}/{hash}           → bytes del PDF

    Attributes:
        _base_url:    URL base de l'API (sense barra final).
        _timeout:     Temps màxim d'espera per resposta en segons.
        _max_retries: Nombre màxim de reintents en cas d'error de xarxa.
    """

    def __init__(self, base_url: str, timeout: int = 30, max_retries: int = 2) -> None:
        """Inicialitza el client amb la configuració de connexió.

        Args:
            base_url:    URL base de l'API (p.ex. 'https://contractaciopublica.cat/portal-api').
            timeout:     Temps màxim d'espera per resposta en segons.
            max_retries: Nombre màxim de reintents en cas d'error de xarxa.
        """
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries

    # ---------------------------------------------------------------------------
    # Implementació del port
    # ---------------------------------------------------------------------------

    def fetch_tenders(self, params: dict) -> list[Tender]:
        """Cerca licitacions a l'API i retorna la pàgina de resultats com a Tenders.

        Descarta els ítems que només tenen la fase ALERTA_FUTURA, perquè no disposen
        de documents i provocarien que el NLP retornés score = 0 (RN-15).

        Args:
            params: Paràmetres de query string per a /cerca-avancada.

        Returns:
            Llista de Tender construïts a partir del camp 'content' de la resposta,
            filtrant els ítems sense ANUNCI_LICITACIO.

        Raises:
            TenderApiError: Si la crida HTTP falla o la resposta és inesperada.
        """
        data = self._get("/cerca-avancada", params=params)
        all_items = data.get("content", [])
        logger.info("[API] Rebuts %d ítems de /cerca-avancada", len(all_items))

        result = []
        for item in all_items:
            if self._te_anunci_licitacio(item):
                result.append(self._parse_tender(item))
            else:
                logger.debug(
                    "[API] Descartat (sense ANUNCI_LICITACIO): expedientId=%s fases=%s",
                    item.get("expedientId"), list(
                        (item.get("fasesVigents") or {}).keys()),
                )

        logger.info("[API] %d ítems passen el filtre ANUNCI_LICITACIO (descartats %d)",
                    len(result), len(all_items) - len(result))
        return result

    def fetch_documents(self, expedient_id: str, publicacio_id: int) -> list[Document]:
        """Obté la llista de documents d'una licitació des del seu detall.

        Args:
            expedient_id:  UUID de l'expedient.
            publicacio_id: Identificador numèric de la publicació.

        Returns:
            Llista de Document extrets de les seccions conegudes del JSON.

        Raises:
            TenderApiError: Si la crida HTTP falla.
        """
        data = self._get(
            f"/detall-publicacio-expedient/{expedient_id}/{publicacio_id}")
        return self._extract_documents(expedient_id, data)

    def download_document(self, doc_id: int, hash: str) -> bytes:  # noqa: A002
        """Descarrega els bytes d'un document PDF.

        Args:
            doc_id: Identificador numèric del document.
            hash:   Hash MD5 (hex) del document, usat per construir l'URL.

        Returns:
            Bytes del fitxer PDF.

        Raises:
            TenderApiError: Si la descàrrega falla.
        """
        return self._get_bytes(f"/descarrega-document/{doc_id}/{hash}")

    # ---------------------------------------------------------------------------
    # Mètodes auxiliars de transport HTTP
    # ---------------------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> dict:
        """Fa una crida GET i retorna el JSON deserialitzat.

        Args:
            path:   Path relatiu a _base_url (amb barra inicial).
            params: Paràmetres de query string opcionals.

        Returns:
            Diccionari JSON de la resposta.

        Raises:
            TenderApiError: Si la crida falla o el servidor retorna un error HTTP.
        """
        url = f"{self._base_url}{path}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            raise TenderApiError(str(exc)) from exc

    def _get_bytes(self, path: str) -> bytes:
        """Fa una crida GET i retorna el contingut en bytes (per PDFs).

        Args:
            path: Path relatiu a _base_url (amb barra inicial).

        Returns:
            Bytes de la resposta.

        Raises:
            TenderApiError: Si la crida falla o el servidor retorna un error HTTP.
        """
        url = f"{self._base_url}{path}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url)
                response.raise_for_status()
                return response.content
        except httpx.HTTPError as exc:
            raise TenderApiError(str(exc)) from exc

    # ---------------------------------------------------------------------------
    # Mètodes de parseo del JSON
    # ---------------------------------------------------------------------------

    # Fases que indiquen que l'expedient té documents i pot ser processat (RN-15).
    # 'ANUNCI_EN_TERMINI' és el nom real que retorna l'API per a faseVigent=30
    # (descobert via logs el 10/05/2026 — diferent del catàleg de Dades Mestres).
    _FASES_AMB_DOCUMENTS = frozenset({"ANUNCI_LICITACIO", "ANUNCI_EN_TERMINI"})

    @classmethod
    def _te_anunci_licitacio(cls, item: dict) -> bool:
        """Retorna True si l'ítem té alguna fase activa amb documents (RN-15).

        Accepta 'ANUNCI_LICITACIO' i 'ANUNCI_EN_TERMINI' (nom real de l'API
        per a faseVigent=30). Els ítems sense 'fasesVigents' (legacy) es
        conserven per compatibilitat. Els que NOMÉS tenen 'ALERTA_FUTURA'
        es descarten perquè no disposen de documents.

        Args:
            item: Element del camp 'content' de /cerca-avancada.

        Returns:
            True si s'ha de conservar l'ítem, False si s'ha de descartar.
        """
        fases = item.get("fasesVigents")
        if fases is None:
            return True
        return bool(cls._FASES_AMB_DOCUMENTS & fases.keys())

    @classmethod
    def _parse_tender(cls, item: dict) -> Tender:
        """Construeix un Tender a partir d'un element del llistat /cerca-avancada.

        Cerca 'idPublicacio' a la primera fase activa trobada (ANUNCI_LICITACIO o
        ANUNCI_EN_TERMINI). Si no n'hi ha cap, usa item['id'] com a fallback (RN-15).

        Args:
            item: Diccionari amb els camps del llistat paginat.

        Returns:
            Tender amb els camps d'identificació emplenats.
        """
        fases = item.get("fasesVigents") or {}
        anunci = next(
            (fases[k] for k in cls._FASES_AMB_DOCUMENTS if k in fases),
            {},
        )
        publicacio_id = anunci.get("idPublicacio") or item["id"]
        return Tender(
            expedient_id=item["expedientId"],
            publicacio_id=publicacio_id,
            organ=item["organ"],
            titol=item["titol"],
        )

    @staticmethod
    def _extract_documents(expedient_id: str, data: dict) -> list[Document]:
        """Extreu tots els documents de les seccions conegudes del JSON de detall.

        Args:
            expedient_id: UUID de l'expedient al qual pertanyen els documents.
            data:         JSON complet de /detall-publicacio-expedient.

        Returns:
            Llista de Document amb doc_type assignat per secció.
        """
        logger.debug(
            "[DETALL] expedient=%s — claus arrel: %s",
            expedient_id, list(data.keys()),
        )
        dades = data.get("dades", {})
        logger.debug(
            "[DETALL] expedient=%s — claus dades: %s",
            expedient_id, list(dades.keys())[:30] if dades else "BUIT",
        )
        publicacio = dades.get("publicacio", {}) if dades else {}
        logger.debug(
            "[DETALL] expedient=%s — claus dades.publicacio: %s",
            expedient_id, list(publicacio.keys())[
                :30] if publicacio else "BUIT",
        )
        dades_pub = publicacio.get("dadesPublicacio", {})
        logger.debug(
            "[DETALL] expedient=%s — claus dades.publicacio.dadesPublicacio: %s",
            expedient_id, list(dades_pub.keys()) if dades_pub else "BUIT",
        )
        documents: list[Document] = []

        for section_key in _DOCUMENT_SECTIONS:
            section = dades_pub.get(section_key, [])
            if isinstance(section, dict):
                if not section:
                    section = []
                elif "docs" in section:
                    section = section["docs"]
                    logger.debug(
                        "[DETALL] expedient=%s — secció '%s' estructura {docs:[...]}, %d docs",
                        expedient_id, section_key, len(section),
                    )
                elif "ca" in section or "es" in section:
                    section = section.get("ca") or section.get("es") or []
                elif "id" in section:
                    section = [section]
                else:
                    logger.warning(
                        "[DETALL] expedient=%s — secció '%s' dict sense estructura coneguda (claus: %s), s'ignora",
                        expedient_id, section_key, list(section.keys())[:5],
                    )
                    section = []
            elif not isinstance(section, list):
                logger.warning(
                    "[DETALL] expedient=%s — secció '%s' tipus inesperat (%s), s'ignora",
                    expedient_id, section_key, type(section).__name__,
                )
                continue
            logger.debug(
                "[DETALL] expedient=%s — secció '%s': %d ítems",
                expedient_id, section_key, len(section),
            )
            doc_type = DocumentType.from_api_section(section_key)
            for raw in section:
                documents.append(Document(
                    expedient_id=expedient_id,
                    doc_id=raw["id"],
                    titol=raw["titol"],
                    hash=raw["hash"],
                    mida=raw["mida"],
                    doc_type=doc_type,
                ))

        logger.debug(
            "[DETALL] expedient=%s — total documents extrets: %d",
            expedient_id, len(documents),
        )
        return documents
