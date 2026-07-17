"""Application processing state machine (architecture §18)."""

from housing_processor.domain.shared.enums import ApplicationStatus
from housing_processor.domain.shared.errors import InvalidStatusTransitionError
from housing_processor.domain.shared.identifiers import ApplicationId

# Allowed transitions: from_status -> frozenset of to_status
_ALLOWED: dict[ApplicationStatus, frozenset[ApplicationStatus]] = {
    ApplicationStatus.RECEIVED: frozenset(
        {
            ApplicationStatus.DUPLICATE,
            ApplicationStatus.EXTRACTING,
        }
    ),
    ApplicationStatus.EXTRACTING: frozenset(
        {
            ApplicationStatus.EXTRACTED,
            ApplicationStatus.FAILED,
        }
    ),
    ApplicationStatus.EXTRACTED: frozenset({ApplicationStatus.MATCHING}),
    ApplicationStatus.MATCHING: frozenset(
        {
            ApplicationStatus.MATCHED,
            ApplicationStatus.REVIEW_REQUIRED,
            ApplicationStatus.FAILED,
        }
    ),
    ApplicationStatus.REVIEW_REQUIRED: frozenset(
        {
            ApplicationStatus.MATCHED,
            ApplicationStatus.DUPLICATE,
        }
    ),
    ApplicationStatus.MATCHED: frozenset({ApplicationStatus.EXPORTED}),
    ApplicationStatus.FAILED: frozenset({ApplicationStatus.EXTRACTING}),
    ApplicationStatus.DUPLICATE: frozenset(),
    ApplicationStatus.EXPORTED: frozenset(),
}


def can_transition(from_status: ApplicationStatus, to_status: ApplicationStatus) -> bool:
    return to_status in _ALLOWED.get(from_status, frozenset())


def assert_can_transition(
    application_id: ApplicationId,
    from_status: ApplicationStatus,
    to_status: ApplicationStatus,
) -> None:
    if not can_transition(from_status, to_status):
        raise InvalidStatusTransitionError(
            application_id=application_id,
            from_status=from_status.value,
            to_status=to_status.value,
        )
