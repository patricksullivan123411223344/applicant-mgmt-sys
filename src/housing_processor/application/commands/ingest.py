from dataclasses import dataclass
from datetime import datetime

from housing_processor.application.dto.actor import ActorContext


@dataclass(frozen=True, slots=True)
class IngestApplicationCommand:
    content: bytes
    filename: str
    actor: ActorContext
    received_at: datetime | None = None
    source: str = "manual_upload"
    idempotency_key: str | None = None
