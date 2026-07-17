from dataclasses import dataclass
from datetime import datetime

from housing_processor.application.dto.actor import ActorContext
from housing_processor.domain.shared.enums import GroupStatus


@dataclass(frozen=True, slots=True)
class CreateExcelExportCommand:
    actor: ActorContext
    include_group_statuses: tuple[GroupStatus, ...] = (
        GroupStatus.INCOMPLETE,
        GroupStatus.ACTIVE,
        GroupStatus.COMPLETE,
        GroupStatus.REVIEW_REQUIRED,
    )
    as_of: datetime | None = None
