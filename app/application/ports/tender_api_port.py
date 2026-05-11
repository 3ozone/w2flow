"""Port (contrato ABC) per accedir a l'API de contractació pública (RF-01, RF-02, RF-04)."""
from abc import ABC, abstractmethod

from app.domain.entities.document import Document
from app.domain.entities.tender import Tender


class TenderApiPort(ABC):
    """Defineix el contracte que ha de complir qualsevol client de l'API externa.

    La infraestructura implementarà aquest port (ContractacioPublicaClient).
    La capa d'aplicació depèn d'aquest contracte, mai de la implementació concreta.
    """

    @abstractmethod
    def fetch_tenders(self, params: dict) -> list[Tender]:
        """Cerca licitacions a l'API amb els paràmetres de filtre natius.

        Args:
            params: Diccionari generat per FilterConfig.to_api_params().

        Returns:
            Llista de Tender construïts a partir de la resposta de l'API.
        """

    @abstractmethod
    def fetch_documents(self, expedient_id: str, publicacio_id: int) -> list[Document]:
        """Recupera la llista de documents adjunts d'una licitació (RF-04).

        Crida l'endpoint /detall-publicacio-expedient i extreu els documents per secció.

        Args:
            expedient_id:  Identificador UUID de l'expedient.
            publicacio_id: Identificador numèric de la publicació.

        Returns:
            Llista de Document amb doc_type, doc_id, hash i metadades.
        """

    @abstractmethod
    def download_document(self, doc_id: int, hash: str) -> bytes:
        """Descarrega el PDF d'un document adjunt a una licitació.

        Args:
            doc_id: Identificador del document (camp `id` del JSON de l'API).
            hash:   Hash del document per a la URL de descàrrega.

        Returns:
            Contingut binari del PDF.
        """
