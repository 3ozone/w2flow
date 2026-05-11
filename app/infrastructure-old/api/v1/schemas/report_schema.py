"""Pydantic schema for comparative report API responses."""

from __future__ import annotations

from pydantic import BaseModel

from app.domain.entities.comparative_report import ComparativeReport
from app.infrastructure.api.v1.schemas.tender_schema import TenderSchema


class ReportSchema(BaseModel):
    """Response schema for a comparative report."""

    total_count: int
    viable_count: int
    tenders: list[TenderSchema]

    @classmethod
    def from_domain(cls, report: ComparativeReport) -> "ReportSchema":
        """Build from a ComparativeReport domain entity."""
        return cls(
            total_count=len(report.scored_tenders),
            viable_count=len(report.get_viable_tenders()),
            tenders=[TenderSchema.from_domain(st) for st in report.scored_tenders],
        )
