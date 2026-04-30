"""Domain entity representing a document attached to a tender."""
from dataclasses import dataclass

from app.domain.value_objects.document_type import DocumentType


@dataclass
class Document:
    """Domain entity representing a document attached to a tender."""

    expedient_id: str
    doc_id: int
    titol: str
    hash: str
    mida_kb: float
    file_path: str
    type: DocumentType

    def __post_init__(self) -> None:
        if not self.expedient_id:
            raise ValueError("expedient_id cannot be empty")
        if not self.titol:
            raise ValueError("titol cannot be empty")
        if self.mida_kb < 0:
            raise ValueError("mida_kb cannot be negative")

    def is_valid_type(self) -> bool:
        """Return True if the document type is known (not UNKNOWN)."""
        return self.type != DocumentType.UNKNOWN

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Document):
            return NotImplemented
        return self.expedient_id == other.expedient_id and self.doc_id == other.doc_id

    def __hash__(self) -> int:
        return hash((self.expedient_id, self.doc_id))
