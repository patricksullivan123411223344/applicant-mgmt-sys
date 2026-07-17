from enum import StrEnum


class ApplicationStatus(StrEnum):
    RECEIVED = "received"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    MATCHING = "matching"
    REVIEW_REQUIRED = "review_required"
    MATCHED = "matched"
    EXPORTED = "exported"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class GroupStatus(StrEnum):
    INCOMPLETE = "incomplete"
    ACTIVE = "active"
    COMPLETE = "complete"
    REVIEW_REQUIRED = "review_required"
    ARCHIVED = "archived"


class MatchDecisionType(StrEnum):
    ATTACH_TO_EXISTING = "attach_to_existing"
    CREATE_NEW_GROUP = "create_new_group"
    REVIEW_REQUIRED = "review_required"


class MatchMethod(StrEnum):
    EXACT_EMAIL = "exact_email"
    EXACT_PHONE = "exact_phone"
    ROOMMATE_REFERENCE = "roommate_reference"
    ROOMMATE_OVERLAP = "roommate_overlap"
    MANUAL = "manual"


class ReviewStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
