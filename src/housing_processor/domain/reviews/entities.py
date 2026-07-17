from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from housing_processor.domain.shared.enums import ReviewStatus
from housing_processor.domain.shared.identifiers import ApplicationId, GroupId, ReviewItemId


@dataclass(slots=True)
class ReviewItem:
    id: ReviewItemId
    application_id: ApplicationId
    status: ReviewStatus
    reason_codes: tuple[str, ...]
    created_at: datetime
    version: int = 1
    suggested_group_id: GroupId | None = None
    resolved_at: datetime | None = None
    resolved_by: UUID | None = None
    resolution_notes: str | None = None
    evidence_summary: list[str] = field(default_factory=list)
