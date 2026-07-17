from dataclasses import dataclass

from housing_processor.application.dto.actor import ActorContext
from housing_processor.domain.shared.identifiers import ApplicationId


@dataclass(frozen=True, slots=True)
class ProcessApplicationCommand:
    application_id: ApplicationId
    actor: ActorContext
    force_reprocess: bool = False
