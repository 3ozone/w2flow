from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EvaluationCompletedEvent:
    """Domain event emitted when a tender evaluation has been completed."""

    expedient_id: str
    total_score: int
    is_viable: bool
    occurred_at: datetime = field(default_factory=datetime.utcnow)
