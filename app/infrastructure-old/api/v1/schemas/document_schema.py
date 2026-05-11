"""Pydantic schema for Document responses."""

from __future__ import annotations

from pydantic import BaseModel

from app.domain.entities.document import Document


class DocumentSchema(BaseModel):
    """Serialized representation of a Document."""

    expedient_id: str
    doc_id: int
    titol: str
    type: str
    mida_kb: float
    file_path: str

    @classmethod
    def from_domain(cls, doc: Document) -> "DocumentSchema":
        return cls(
            expedient_id=doc.expedient_id,
            doc_id=doc.doc_id,
            titol=doc.titol,
            type=doc.type.value,
            mida_kb=doc.mida_kb,
            file_path=doc.file_path,
        )
