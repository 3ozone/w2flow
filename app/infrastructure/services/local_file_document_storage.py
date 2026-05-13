"""Implementació local del port DocumentStoragePort — desa PDFs a disc (RF-09)."""
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.application.ports.document_storage_port import DocumentStoragePort
from app.domain.entities.tender_document import TenderDocument

logger = logging.getLogger(__name__)


class LocalFileDocumentStorage(DocumentStoragePort):
    """Guarda i recupera documents PDF al sistema de fitxers local.

    Cada licitació té el seu propi directori: ``<base_dir>/<expedient_id>/``.
    El directori es crea automàticament si no existeix.

    Args:
        base_dir: Directori arrel on es desaran els documents (p. ex. ``Path("downloads")``).
    """

    def __init__(self, base_dir: Path) -> None:
        """Inicialitza l'emmagatzematge local amb el directori base indicat.

        Args:
            base_dir: Ruta al directori arrel per als documents descarregats.
        """
        self._base_dir = base_dir

    def save(self, expedient_id: str, filename: str, content: bytes) -> TenderDocument:
        """Desa el contingut binari a ``<base_dir>/<expedient_id>/<filename>``.

        Crea el directori si no existeix. Si el fitxer ja existeix, el sobreescriu.

        Args:
            expedient_id: UUID de la licitació.
            filename:     Nom del fitxer (p. ex. ``PCAP.pdf``).
            content:      Contingut binari del PDF.

        Returns:
            TenderDocument amb la ruta relativa i la data de creació.
        """
        target_dir = self._base_dir / expedient_id
        target_dir.mkdir(parents=True, exist_ok=True)
        filepath = target_dir / filename
        filepath.write_bytes(content)
        logger.debug("[Storage] Desat %s/%s (%d bytes)", expedient_id, filename, len(content))
        return TenderDocument(
            expedient_id=expedient_id,
            filename=filename,
            filepath=str(filepath),
            created_at=datetime.now(tz=timezone.utc),
        )

    def list_documents(self, expedient_id: str) -> list[str]:
        """Retorna els noms dels fitxers desats per a un expedient.

        Args:
            expedient_id: UUID de la licitació.

        Returns:
            Llista de noms de fitxer ordenada alfabèticament. Buida si no hi ha documents.
        """
        target_dir = self._base_dir / expedient_id
        if not target_dir.exists():
            return []
        return sorted(f.name for f in target_dir.iterdir() if f.is_file())

    def delete(self, expedient_id: str, filename: str) -> None:
        """Elimina el fitxer ``<base_dir>/<expedient_id>/<filename>`` del disc.

        No llança error si el fitxer no existeix.

        Args:
            expedient_id: UUID de la licitació.
            filename:     Nom del fitxer a eliminar.
        """
        filepath = self._base_dir / expedient_id / filename
        if filepath.exists():
            filepath.unlink()
            logger.debug("[Storage] Eliminat %s/%s", expedient_id, filename)
