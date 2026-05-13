"""Entitat de domini que representa un document adjunt d'una licitació (RF-09, RF-10)."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TenderDocument:
    """Un document PDF adjunt a una licitació, descarregat i persistit a disc.

    Cada instància correspon a un fitxer descarregat durant el pipeline.
    El camp ``comentari_llm`` s'omple en una fase posterior quan el LLM
    analitza el document per generar un comentari narratiu (RF-10).

    Attributes:
        expedient_id:  UUID de la licitació a la qual pertany el document.
        filename:      Nom del fitxer (p. ex. ``PCAP.pdf``).
        filepath:      Ruta relativa al fitxer al disc (p. ex. ``downloads/exp-001/PCAP.pdf``).
        comentari_llm: Comentari narratiu generat pel LLM sobre el document, o ``None``
                       si encara no s'ha analitzat.
        created_at:    Data i hora en què es va descarregar el document.
    """

    expedient_id: str
    filename: str
    filepath: str
    created_at: datetime
    comentari_llm: str | None = field(default=None)

    def __post_init__(self) -> None:
        """Valida que els camps obligatoris no siguin buits."""
        if not self.expedient_id:
            raise ValueError("expedient_id no pot ser buit.")
        if not self.filename:
            raise ValueError("filename no pot ser buit.")

    def te_comentari(self) -> bool:
        """Retorna ``True`` si el document ja té un comentari LLM assignat."""
        return self.comentari_llm is not None
