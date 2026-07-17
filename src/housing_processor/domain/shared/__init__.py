"""Shared domain primitives: identifiers, enums, value objects, errors."""

from housing_processor.domain.shared.enums import (
    ApplicationStatus,
    GroupStatus,
    MatchDecisionType,
    MatchMethod,
    ReviewStatus,
)
from housing_processor.domain.shared.errors import (
    ContactMustBeGroupMemberError,
    DomainError,
    DuplicateGroupMemberError,
    InvalidStatusTransitionError,
    ResourceNotFoundError,
    VersionConflictError,
)
from housing_processor.domain.shared.identifiers import (
    ApplicantId,
    ApplicationId,
    GroupId,
    PropertyId,
    ReviewItemId,
)
from housing_processor.domain.shared.value_objects import (
    ConfidenceScore,
    EmailAddress,
    PersonName,
    PhoneNumber,
)

__all__ = [
    "ApplicantId",
    "ApplicationId",
    "ApplicationStatus",
    "ConfidenceScore",
    "ContactMustBeGroupMemberError",
    "DomainError",
    "DuplicateGroupMemberError",
    "EmailAddress",
    "GroupId",
    "GroupStatus",
    "InvalidStatusTransitionError",
    "MatchDecisionType",
    "MatchMethod",
    "PersonName",
    "PhoneNumber",
    "PropertyId",
    "ResourceNotFoundError",
    "ReviewItemId",
    "ReviewStatus",
    "VersionConflictError",
]
