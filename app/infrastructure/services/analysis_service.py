"""Analysis service — narrative comparative analysis via Timbal agent."""

from __future__ import annotations

import json

from timbal import Agent
from timbal.types.file import File

from app.application.ports.analysis_port import AnalysisPort
from app.domain.entities.scored_tender import ScoredTender

_SYSTEM_PROMPT = """Eres un experto en licitaciones públicas catalanas trabajando para una empresa de ingeniería y construcción.
Para cada licitación recibida, con sus documentos adjuntos, formatea así:

---
📋 **[Título del contrato]**
🏛️ Órgano: [nombre del organismo]
💰 Presupuesto: [importe] €
📅 Publicación: [fecha]
🔖 Fase: [fase actual]
🔗 Expediente: [código expediente]
🎯 **Puntuación: [score.total]/70 — [score.recomanacio]**
   - Presupuesto: [score.detall.pressupost] pts
   - Sector relevante: [score.detall.sector_positiu] pts
   - Penalizaciones IT/software: [score.detall.sector_negatiu] pts
   - Procedimiento abierto: [score.detall.procediment_obert] pts
   - Subcontratación permitida: [score.detall.subcontractació] pts
   - Palabras clave encontradas: [score.paraules_clau_trobades]

📁 Documentos:
  - [nombre] ([tamaño KB])
    → Resumen breve del contenido del documento

---

Al final, ordena las licitaciones por puntuación (mayor a menor) y añade un resumen ejecutivo de cuáles son más interesantes para una empresa de ingeniería/construcción."""


def _build_prompt(scored_tenders: list[ScoredTender], pdf_paths: list[str]) -> str:
    """Build the text prompt with tender data as JSON."""
    tenders_data = []
    for st in scored_tenders:
        tenders_data.append({
            "expedient_id": st.tender.expedient_id,
            "titol": st.tender.titol,
            "organ": st.tender.organ,
            "pressupost": st.tender.pressupost,
            "data_publicacio": st.tender.data_publicacio.isoformat(),
            "fase": st.tender.fase,
            "codi_expedient": st.tender.codi_expedient,
            "score": {
                "total": st.score.total,
                "recomanacio": st.score.recomanacio,
                "detall": st.score.detall,
                "paraules_clau_trobades": list(st.score.paraules_clau_trobades),
                "penalitzacions": list(st.score.penalitzacions),
            },
        })
    return (
        f"Licitacions a analitzar ({len(scored_tenders)}):\n\n"
        f"{json.dumps(tenders_data, ensure_ascii=False, indent=2)}\n\n"
        f"Documents disponibles: {pdf_paths}"
    )


class AnalysisService(AnalysisPort):
    """Uses a Timbal Agent to generate a narrative comparative analysis."""

    def __init__(self, model: str = "google/gemini-2.5-flash") -> None:
        self._agent = Agent(
            name="AnalysisAgent",
            model=model,
            system_prompt=_SYSTEM_PROMPT,
        )

    async def analyze(
        self,
        scored_tenders: list[ScoredTender],
        pdf_paths: list[str],
    ) -> str:
        """Call the Timbal agent and return the narrative analysis text."""
        prompt = _build_prompt(scored_tenders, pdf_paths)

        files = []
        for path in pdf_paths:
            try:
                files.append(File.from_path(path))
            except Exception:
                pass

        kwargs: dict = {"prompt": prompt}
        if files:
            kwargs["files"] = files

        result = await self._agent(**kwargs).collect()

        if result.output is None:
            return ""

        return result.output.collect_text()
