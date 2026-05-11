"""ScoreTenderCommand and its handler."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports.tender_repository_port import TenderRepositoryPort
from app.domain.entities.scored_tender import ScoredTender
from app.domain.entities.tender import Tender
from app.domain.value_objects.filter_config import FilterConfig
from app.domain.value_objects.score import Score

_SECTOR_POSITIU = (
    "obres", "construcció", "infraestructura", "reforma", "rehabilitació",
    "urbanisme", "enginyeria", "instal·lació", "instal.lació", "maquinari",
    "manteniment", "obra civil", "edificació", "pavimentació", "canalització",
    "xarxa", "electricitat", "fontaneria", "climatització", "ascensor",
    "estructura", "fonamentació", "maquinaria escènica", "maquinaria",
)

_SECTOR_NEGATIU = (
    "software", "saas", "plataforma digital", "aplicació web",
    "recursos humans", "nòmina", "gestió de persones", "assegurança",
    "servei jurídic", "auditoria financera", "consultoria de gestió",
)


@dataclass
class ScoreTenderCommand:
    """Command to score a single tender given its extracted PDF texts."""

    tender: Tender
    filter_config: FilterConfig
    pdf_texts: list[str]


class ScoreTenderCommandHandler:
    """Calculates a viability Score for a Tender and persists the ScoredTender."""

    def __init__(self, repository: TenderRepositoryPort) -> None:
        self._repository = repository

    async def handle(self, command: ScoreTenderCommand) -> ScoredTender:
        """Score the tender and persist the result."""
        score = self._calculate_score(command.tender, command.pdf_texts)
        scored = ScoredTender(tender=command.tender,
                              score=score, requirements=None)
        await self._repository.save_scored(scored)
        return scored

    def _calculate_score(self, tender: Tender, pdf_texts: list[str]) -> Score:
        text = tender.titol.lower() + " " + " ".join(pdf_texts).lower()

        # Pressupost (5–30 pts); None = budget not published → 0 pts
        pressupost = tender.pressupost or 0.0
        if pressupost >= 1_000_000:
            pts_pressupost = 30
        elif pressupost >= 500_000:
            pts_pressupost = 25
        elif pressupost >= 100_000:
            pts_pressupost = 15
        else:
            pts_pressupost = 5

        # Sector positiu (+5 per keyword, max 40)
        hits_pos = tuple(kw for kw in _SECTOR_POSITIU if kw in text)
        pts_sector_pos = min(len(hits_pos) * 5, 40)

        # Sector negatiu (-10 per keyword)
        hits_neg = tuple(kw for kw in _SECTOR_NEGATIU if kw in text)
        pts_sector_neg = len(hits_neg) * -10

        # Procediment obert (+20)
        pts_procediment = 20 if "procediment obert" in text else 0

        # Subcontractació (+10)
        pts_subcontract = 10 if "subcontract" in text else 0

        total = max(
            0,
            pts_pressupost + pts_sector_pos + pts_sector_neg
            + pts_procediment + pts_subcontract,
        )

        if total >= 70:
            recomanacio = "RECOMANADA"
        elif total >= 40:
            recomanacio = "A VALORAR"
        else:
            recomanacio = "NO RECOMANADA"

        return Score(
            expedient_id=tender.expedient_id,
            total=total,
            detall={
                "pressupost": pts_pressupost,
                "sector_positiu": pts_sector_pos,
                "sector_negatiu": pts_sector_neg,
                "procediment_obert": pts_procediment,
                "subcontractació": pts_subcontract,
            },
            paraules_clau_trobades=hits_pos,
            penalitzacions=hits_neg,
            recomanacio=recomanacio,
        )
