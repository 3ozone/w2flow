from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProcessFailedEvent:
    """Domain event emitted when the tender processing pipeline fails."""

    reason: str
    expedient_id: str | None = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)
