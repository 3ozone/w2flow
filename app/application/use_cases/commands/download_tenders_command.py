"""DownloadTendersCommand and its handler."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from app.application.ports.licitacion_api_port import LicitationApiPort
from app.application.ports.tender_repository_port import TenderRepositoryPort
from app.domain.entities.tender import Tender
from app.domain.exceptions.download_error import DownloadError
from app.domain.exceptions.duplicate_tender_error import DuplicateTenderError
from app.domain.value_objects.filter_config import FilterConfig

log = logging.getLogger(__name__)


@dataclass
class DownloadTendersCommand:
    """Command to download tenders from the external API."""

    filter_config: FilterConfig


class DownloadTendersCommandHandler:
    """Fetches a page of tenders from the API, filters them and persists each one."""

    def __init__(self, api: LicitationApiPort, repository: TenderRepositoryPort) -> None:
        self._api = api
        self._repository = repository

    async def handle(self, command: DownloadTendersCommand) -> list[Tender]:
        """Execute the command and return the list of downloaded Tender entities."""
        try:
            raw_items = await self._api.fetch_page(command.filter_config, 0)
        except Exception as exc:
            raise DownloadError(str(exc)) from exc

        tenders: list[Tender] = []
        log.info("[DOWNLOAD] fetch_page returned %d raw items", len(raw_items))
        for item in raw_items:
            # Extract fase and dataPublicacio from fasesVigents (real API shape)
            fases_vigents: dict = item.get("fasesVigents") or {}
            fase = next(iter(fases_vigents), "") if fases_vigents else ""
            fase_data = fases_vigents.get(fase, {}) if fase else {}
            data_pub_raw: str = (fase_data.get("dataPublicacio") or "")[:10]
            try:
                data_publicacio = date.fromisoformat(
                    data_pub_raw) if data_pub_raw else date.today()
            except ValueError:
                data_publicacio = date.today()

            # If pressupost is null in the listing, fetch the detail for the real value
            pressupost_raw = item.get("pressupostLicitacio")
            if pressupost_raw is None:
                try:
                    detail = await self._api.fetch_detail(item["expedientId"], item["id"])
                    pressupost_raw = detail.get("pressupostLicitacio")
                except DownloadError as exc:
                    log.warning(
                        "[DOWNLOAD] fetch_detail failed for %s/%s — skipping: %s",
                        item.get("expedientId"), item.get("id"), exc,
                    )
                    continue

            tender = Tender(
                expedient_id=item["expedientId"],
                publicacio_id=item["id"],
                titol=item.get("titol") or item.get(
                    "nomPublicacioAgregada") or "Sense títol",
                organ=item.get("organ") or "",
                pressupost=float(pressupost_raw or 0.0),
                codi_expedient=item.get("codiExpedient") or "",
                fase=fase,
                data_publicacio=data_publicacio,
            )
            if not command.filter_config.matches({"pressupost": tender.pressupost}):
                log.info("[DOWNLOAD] SKIP pressupost filter: %s (%.0f < %.0f)",
                         tender.expedient_id, tender.pressupost, command.filter_config.min_pressupost)
                continue
            try:
                await self._repository.save(tender)
            except DuplicateTenderError:
                pass  # RN-06: already in DB, but still include for scoring
            tenders.append(tender)

        return tenders
