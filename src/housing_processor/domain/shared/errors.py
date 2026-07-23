from housing_processor.domain.shared.identifiers import ApplicantId, ApplicationId, GroupId


class DomainError(Exception):
    """Base class for domain rule violations."""

    code: str = "domain.error"

    def __init__(
        self,
        message: str,
        *,
        context: dict[str, object] | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}
        if code is not None:
            self.code = code


class ResourceNotFoundError(DomainError):
    code = "resource.not_found"


class ApplicantInGroupError(DomainError):
    code = "applicant.in_group"

    def __init__(self, applicant_id: ApplicantId) -> None:
        super().__init__(
            "Cannot delete an applicant who is still a member of a housing group. "
            "Remove them from the group first.",
            context={"applicant_id": str(applicant_id)},
            code="applicant.in_group",
        )
        self.applicant_id = applicant_id


class VersionConflictError(DomainError):
    code = "resource.version_conflict"


class DuplicateGroupMemberError(DomainError):
    code = "group.duplicate_member"

    def __init__(self, applicant_id: ApplicantId) -> None:
        super().__init__(
            f"Applicant {applicant_id} is already a member of this group.",
            context={"applicant_id": str(applicant_id)},
        )
        self.applicant_id = applicant_id


class ContactMustBeGroupMemberError(DomainError):
    code = "group.contact_not_member"

    def __init__(self, applicant_id: ApplicantId) -> None:
        super().__init__(
            "The selected contact person is not a member of this group.",
            context={"contact_applicant_id": str(applicant_id)},
        )
        self.applicant_id = applicant_id


class InvalidStatusTransitionError(DomainError):
    code = "application.invalid_status_transition"

    def __init__(self, *, application_id: ApplicationId, from_status: str, to_status: str) -> None:
        super().__init__(
            f"Cannot transition application from '{from_status}' to '{to_status}'.",
            context={
                "application_id": str(application_id),
                "from_status": from_status,
                "to_status": to_status,
            },
        )


class DuplicateGroupMemberInGroupError(DuplicateGroupMemberError):
    """Alias retained for clarity at call sites."""


class GroupNotFoundError(ResourceNotFoundError):
    def __init__(self, group_id: GroupId) -> None:
        super().__init__(
            f"Group {group_id} was not found.",
            context={"group_id": str(group_id)},
        )
