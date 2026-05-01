"""NLP service — extracts structured requirements from tender documents using Timbal."""

from __future__ import annotations

from timbal import Agent

from app.domain.value_objects.requirements import Requirements

_SYSTEM_PROMPT = (
    "Ets un analista expert en contractació pública catalana. "
    "Analitza el text dels documents d'una licitació i extreu els requisits estructurats. "
    "Respon SEMPRE en aquest format exacte (una línia per camp):\n"
    "SOLVENCY_REQUIREMENTS: <text o buit>\n"
    "TECHNICAL_REQUIREMENTS: <text o buit>\n"
    "ADJUDICATION_CRITERIA: <text o buit>\n"
    "SPECIAL_CLAUSES: <text o buit>\n"
)


def _parse_output(raw: str, expedient_id: str) -> Requirements:
    """Parse the structured LLM output into a Requirements value object."""
    lines: dict[str, list[str]] = {
        "SOLVENCY_REQUIREMENTS": [],
        "TECHNICAL_REQUIREMENTS": [],
        "ADJUDICATION_CRITERIA": [],
        "SPECIAL_CLAUSES": [],
    }
    for line in raw.splitlines():
        for key in lines:
            prefix = f"{key}:"
            if line.startswith(prefix):
                value = line[len(prefix):].strip()
                if value:
                    lines[key].append(value)
    return Requirements(
        expedient_id=expedient_id,
        solvency_requirements=tuple(lines["SOLVENCY_REQUIREMENTS"]),
        technical_requirements=tuple(lines["TECHNICAL_REQUIREMENTS"]),
        adjudication_criteria=tuple(lines["ADJUDICATION_CRITERIA"]),
        special_clauses=tuple(lines["SPECIAL_CLAUSES"]),
        raw_agent_output=raw,
    )


class NlpService:
    """Uses a Timbal Agent to extract structured requirements from tender PDF texts."""

    def __init__(self, model: str = "google/gemini-2.5-flash") -> None:
        self._agent = Agent(
            name="NlpRequirementsAgent",
            model=model,
            system_prompt=_SYSTEM_PROMPT,
        )

    async def extract_requirements(
        self,
        expedient_id: str,
        pdf_texts: list[str],
    ) -> Requirements:
        """Call the LLM agent and return a Requirements value object."""
        combined = "\n\n---\n\n".join(pdf_texts)
        prompt = (
            f"Expedient: {expedient_id}\n\n"
            f"Text dels documents:\n\n{combined}"
        )
        result = await self._agent(prompt=prompt).collect()

        if result.output is None:
            return Requirements(
                expedient_id=expedient_id,
                solvency_requirements=(),
                technical_requirements=(),
                adjudication_criteria=(),
                special_clauses=(),
                raw_agent_output="",
            )

        raw = result.output.collect_text()
        return _parse_output(raw, expedient_id)
