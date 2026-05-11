from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TenderDownloadedEvent:
    """Domain event emitted when a tender has been successfully downloaded."""

    expedient_id: str
    publicacio_id: int
    occurred_at: datetime = field(default_factory=datetime.utcnow)
