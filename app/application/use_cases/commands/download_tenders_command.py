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

    _PAGE_SIZE: int = 20

    async def handle(self, command: DownloadTendersCommand) -> list[Tender]:
        """Execute the command and return the list of downloaded Tender entities."""
        tenders: list[Tender] = []
        page = 0
        max_results = command.filter_config.max_results

        while len(tenders) < max_results:
            try:
                raw_items = await self._api.fetch_page(command.filter_config, page)
            except Exception as exc:
                raise DownloadError(str(exc)) from exc

            log.info(
                "[DOWNLOAD] page=%d fetch_page returned %d raw items", page, len(raw_items))

            if not raw_items:
                break

            for item in raw_items:
                if len(tenders) >= max_results:
                    break

                # Extract fase and dataPublicacio from fasesVigents (real API shape)
                fases_vigents: dict = item.get("fasesVigents") or {}
                fase = next(iter(fases_vigents), "") if fases_vigents else ""
                fase_data = fases_vigents.get(fase, {}) if fase else {}
                data_pub_raw: str = (fase_data.get(
                    "dataPublicacio") or "")[:10]
                try:
                    data_publicacio = date.fromisoformat(
                        data_pub_raw) if data_pub_raw else date.today()
                except ValueError:
                    data_publicacio = date.today()

                # Always fetch detail to get pressupost + optional fields (cpv, termini, data_limit)
                pressupost_raw = item.get("pressupostLicitacio")
                codi_cpv: str | None = None
                termini_execucio: str | None = None
                data_limit_presentacio: str | None = None
                try:
                    detail = await self._api.fetch_detail(item["expedientId"], item["id"])
                    dades_pub = (detail.get("publicacio") or {}
                                 ).get("dadesPublicacio") or {}
                    if pressupost_raw is None:
                        pressupost_raw = dades_pub.get(
                            "pressupostLicitacio") or None
                    dl_raw = dades_pub.get(
                        "dataTerminiPresentacioOSolicitud") or ""
                    data_limit_presentacio = dl_raw[:10] if dl_raw else None
                    lots = (detail.get("publicacio") or {}).get(
                        "dadesPublicacioLot") or []
                    if lots:
                        lot = lots[0]
                        cpv = lot.get("cpvPrincipal") or {}
                        codi_cpv = cpv.get("codi") or None
                        durada = lot.get("duradaTermini") or {}
                        if durada.get("esDurada"):
                            parts = []
                            if durada.get("anys"):
                                parts.append(f"{durada['anys']} anys")
                            if durada.get("mesos"):
                                parts.append(f"{durada['mesos']} mesos")
                            if durada.get("dies"):
                                parts.append(f"{durada['dies']} dies")
                            termini_execucio = " ".join(
                                parts) if parts else None
                except DownloadError as exc:
                    if pressupost_raw is None:
                        log.warning(
                            "[DOWNLOAD] fetch_detail failed for %s/%s — skipping: %s",
                            item.get("expedientId"), item.get("id"), exc,
                        )
                        continue
                    log.warning(
                        "[DOWNLOAD] fetch_detail failed for %s/%s — continuing without optional fields: %s",
                        item.get("expedientId"), item.get("id"), exc,
                    )

                tender = Tender(
                    expedient_id=item["expedientId"],
                    publicacio_id=item["id"],
                    titol=item.get("titol") or item.get(
                        "nomPublicacioAgregada") or "Sense títol",
                    organ=item.get("organ") or "",
                    pressupost=float(
                        pressupost_raw) if pressupost_raw is not None else None,
                    codi_expedient=item.get("codiExpedient") or "",
                    fase=fase,
                    data_publicacio=data_publicacio,
                    codi_cpv=codi_cpv,
                    termini_execucio=termini_execucio,
                    data_limit_presentacio=data_limit_presentacio,
                )
                if not command.filter_config.matches({"pressupost": tender.pressupost, "fase": tender.fase}):
                    log.info("[DOWNLOAD] SKIP pressupost filter: %s (%s < %.0f)",
                             tender.expedient_id, tender.pressupost, command.filter_config.min_pressupost)
                    continue
                try:
                    await self._repository.save(tender)
                except DuplicateTenderError:
                    pass  # RN-06: already in DB, but still include for scoring
                except Exception as exc:
                    log.warning(
                        "[DOWNLOAD] Could not persist tender %s — skipping: %s",
                        tender.expedient_id, exc,
                    )
                    continue
                tenders.append(tender)

            # Stop pagination when page returned fewer items than a full page
            if len(raw_items) < self._PAGE_SIZE:
                break

            page += 1

        return tenders
