"""Value object representing the type of a document attached to a tender (RN-02)."""
from enum import Enum


class DocumentType(Enum):
    """Classification of a document attached to a tender.

    Mandatory types (RN-02): PCAP, PPT, TECHNICAL_MEMORY, BUDGET, ANNEXES.
    Any document section not explicitly mapped is classified as UNKNOWN.

    The type is resolved from the API JSON section key via :meth:`from_api_section`.
    Confirmed section keys (empirical):
      - ``plecsDeClausulesAdministratives`` → PCAP
      - ``plecsDePrescripcionsTecniques``   → PPT
      - ``memoriaJustificativaContracte``   → TECHNICAL_MEMORY
    BUDGET and ANNEXES have no dedicated section confirmed yet.
    """

    PCAP = "pcap"
    PPT = "ppt"
    TECHNICAL_MEMORY = "technical_memory"
    BUDGET = "budget"
    ANNEXES = "annexes"
    UNKNOWN = "unknown"

    @classmethod
    def from_api_section(cls, section_key: str) -> "DocumentType":
        """Return the document type that corresponds to an API JSON section key.

        Args:
            section_key: Key from the ``dadesPublicacio`` object in the
                detall-publicacio-expedient response
                (e.g. ``"plecsDeClausulesAdministratives"``).

        Returns:
            The matching :class:`DocumentType`, or :attr:`UNKNOWN` if the
            section key is not explicitly mapped.
        """
        section_map = {
            "plecsDeClausulesAdministratives": cls.PCAP,
            "plecsDePrescripcionsTecniques": cls.PPT,
            "memoriaJustificativaContracte": cls.TECHNICAL_MEMORY,
        }
        return section_map.get(section_key, cls.UNKNOWN)
