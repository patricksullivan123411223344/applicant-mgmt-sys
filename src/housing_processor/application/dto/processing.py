from dataclasses import dataclass

from housing_processor.domain.shared.enums import ApplicationStatus
from housing_processor.domain.shared.identifiers import (
    ApplicantId,
    ApplicationId,
    GroupId,
    ReviewItemId,
)


@dataclass(frozen=True, slots=True)
class ProcessApplicationResult:
    application_id: ApplicationId
    status: ApplicationStatus
    applicant_id: ApplicantId | None
    group_id: GroupId | None
    group_number: int | None
    review_item_id: ReviewItemId | None
    warnings: tuple[str, ...]
