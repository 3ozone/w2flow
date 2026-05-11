"""Data Transfer Object for Document, used in the application layer."""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.document import Document
from app.domain.value_objects.document_type import DocumentType


@dataclass
class DocumentDTO:
    """Application-layer DTO for the Document entity."""

    expedient_id: str
    doc_id: int
    titol: str
    hash: str
    mida_kb: float
    file_path: str
    type: str  # DocumentType.value string

    @classmethod
    def from_domain(cls, document: Document) -> DocumentDTO:
        """Create a DTO from a domain Document entity."""
        return cls(
            expedient_id=document.expedient_id,
            doc_id=document.doc_id,
            titol=document.titol,
            hash=document.hash,
            mida_kb=document.mida_kb,
            file_path=document.file_path,
            type=document.type.value,
        )

    def to_domain(self) -> Document:
        """Convert this DTO back to a domain Document entity."""
        return Document(
            expedient_id=self.expedient_id,
            doc_id=self.doc_id,
            titol=self.titol,
            hash=self.hash,
            mida_kb=self.mida_kb,
            file_path=self.file_path,
            type=DocumentType(self.type),
        )
