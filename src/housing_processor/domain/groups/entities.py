from dataclasses import dataclass, field
from datetime import datetime

from housing_processor.domain.shared.enums import GroupStatus, MatchMethod
from housing_processor.domain.shared.errors import (
    ContactMustBeGroupMemberError,
    DuplicateGroupMemberError,
)
from housing_processor.domain.shared.identifiers import ApplicantId, ApplicationId, GroupId
from housing_processor.domain.shared.value_objects import ConfidenceScore


@dataclass(slots=True)
class GroupMember:
    applicant_id: ApplicantId
    is_contact: bool
    match_method: MatchMethod
    match_confidence: ConfidenceScore
    source_application_id: ApplicationId
    joined_at: datetime


@dataclass(slots=True)
class HousingGroup:
    id: GroupId
    group_number: int
    status: GroupStatus
    first_application_received_at: datetime
    members: list[GroupMember] = field(default_factory=list)
    version: int = 1

    def add_member(self, member: GroupMember) -> None:
        if any(existing.applicant_id == member.applicant_id for existing in self.members):
            raise DuplicateGroupMemberError(member.applicant_id)
        self.members.append(member)

    def set_contact(self, applicant_id: ApplicantId) -> None:
        if not any(member.applicant_id == applicant_id for member in self.members):
            raise ContactMustBeGroupMemberError(applicant_id)
        for member in self.members:
            member.is_contact = member.applicant_id == applicant_id
