from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Immutable audit record for consequential mutations."""

    event_type: str
    occurred_at: datetime
    actor_id: UUID | None
    request_id: str | None
    entity_type: str
    entity_id: str
    payload: dict[str, object] = field(default_factory=dict)
