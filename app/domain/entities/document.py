"""Domain entity representing a PDF document attached to a tender (RF-04, RN-02)."""
from dataclasses import dataclass

from app.domain.value_objects.document_type import DocumentType

_MANDATORY_TYPES = {DocumentType.PCAP,
                    DocumentType.PPT, DocumentType.TECHNICAL_MEMORY}


@dataclass
class Document:
    """Un document PDF adjunt a una licitació descarregat de contractaciopublica.cat.

    Attributes:
        expedient_id: UUID de la licitació a la qual pertany (clau forana lògica).
        doc_id:       Identificador numèric del document a l'API.
        titol:        Títol tal com apareix a la resposta JSON.
        hash:         Hash MD5 (hex) usat per construir l'URL de descàrrega.
        mida:         Mida del fitxer en bytes.
        doc_type:     Classificació semàntica derivada de la secció JSON de l'API.
    """

    expedient_id: str
    doc_id: int
    titol: str
    hash: str
    mida: int
    doc_type: DocumentType

    def is_mandatory(self) -> bool:
        """Retorna True si el document és obligatori per avaluar la licitació (RN-02)."""
        return self.doc_type in _MANDATORY_TYPES
