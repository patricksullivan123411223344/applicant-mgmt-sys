from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from housing_processor.domain.shared.enums import ApplicationStatus
from housing_processor.domain.shared.identifiers import ApplicationId, GroupId, ReviewItemId


@dataclass(slots=True)
class ApplicationRecord:
    """Domain representation of an ingested application file and its processing state."""

    id: ApplicationId
    file_hash: str
    original_filename: str
    storage_key: str
    status: ApplicationStatus
    received_at: datetime
    source: str
    version: int = 1
    duplicate_of_application_id: ApplicationId | None = None
    group_id: GroupId | None = None
    review_item_id: ReviewItemId | None = None
    parser_version: str | None = None
    matcher_version: str | None = None
    failure_reason: str | None = None
    warnings: list[str] = field(default_factory=list)
    idempotency_key: str | None = None
    created_by: UUID | None = None
