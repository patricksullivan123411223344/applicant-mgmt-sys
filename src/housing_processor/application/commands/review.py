from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from housing_processor.application.dto.actor import ActorContext
from housing_processor.domain.shared.identifiers import ApplicationId, GroupId, ReviewItemId


@dataclass(frozen=True, slots=True)
class ResolveReviewCommand:
    review_item_id: ReviewItemId
    actor: ActorContext
    action: Literal["attach_to_group", "create_group", "mark_duplicate", "reject_application"]
    expected_review_version: int
    group_id: GroupId | None = None
    duplicate_of_application_id: ApplicationId | None = None
    reason_code: str | None = None
    notes: str | None = None
    resolved_by: UUID | None = None
