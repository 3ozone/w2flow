"""Value object representing the structured requirements extracted from a tender by the LLM agent."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Requirements:
    """Structured output from the LLM agent analyzing a tender's requirements."""

    expedient_id: str
    solvency_requirements: tuple[str, ...]
    technical_requirements: tuple[str, ...]
    adjudication_criteria: tuple[str, ...]
    special_clauses: tuple[str, ...]
    raw_agent_output: str

    def is_empty(self) -> bool:
        """Return True if all requirement lists and raw output are empty."""
        return (
            not self.solvency_requirements
            and not self.technical_requirements
            and not self.adjudication_criteria
            and not self.special_clauses
            and not self.raw_agent_output
        )

    def to_dict(self) -> dict:
        """Return a serializable representation of the requirements."""
        return {
            "expedient_id": self.expedient_id,
            "solvency_requirements": list(self.solvency_requirements),
            "technical_requirements": list(self.technical_requirements),
            "adjudication_criteria": list(self.adjudication_criteria),
            "special_clauses": list(self.special_clauses),
            "raw_agent_output": self.raw_agent_output,
        }
