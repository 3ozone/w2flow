"""Value object representing the type of a document attached to a tender."""
from enum import Enum


class DocumentType(Enum):
    """Classification of a document attached to a tender.

    The type is inferred from the document title (``titol`` field returned
    by the contractaciopublica.cat API) via :meth:`from_title`.
    """

    PCAP = "pcap"
    PPT = "ppt"
    TECHNICAL_MEMORY = "technical_memory"
    BUDGET = "budget"
    ANNEXES = "annexes"
    UNKNOWN = "unknown"

    @classmethod
    def from_title(cls, titol: str) -> "DocumentType":
        """Infer the document type from its title using case-insensitive keyword matching.

        Keyword rules (evaluated in order):

        * ``pcap``                              → :attr:`PCAP`
        * ``ppt``                               → :attr:`PPT`
        * ``memor``                             → :attr:`TECHNICAL_MEMORY`
        * ``pressupost``, ``presupuesto``, ``budget`` → :attr:`BUDGET`
        * ``annex``, ``anexo``, ``anex``        → :attr:`ANNEXES`
        * *(no match)*                          → :attr:`UNKNOWN`

        Args:
            titol: The document title as returned by the API (e.g. ``"PCAP_exp_123.pdf"``).

        Returns:
            The matching :class:`DocumentType`, or :attr:`UNKNOWN` if no keyword matches.
        """
        lower = titol.lower()

        if "pcap" in lower:
            return cls.PCAP
        if "ppt" in lower:
            return cls.PPT
        if "memor" in lower:
            return cls.TECHNICAL_MEMORY
        if "pressupost" in lower or "presupuesto" in lower or "budget" in lower:
            return cls.BUDGET
        if "annex" in lower or "anexo" in lower or "anex" in lower:
            return cls.ANNEXES

        return cls.UNKNOWN
