from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ActorContext:
    actor_id: UUID
    role: str
    request_id: str
