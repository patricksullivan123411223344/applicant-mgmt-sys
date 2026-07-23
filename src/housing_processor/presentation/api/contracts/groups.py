from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from housing_processor.domain.shared.enums import GroupStatus


class GroupSummaryResponse(BaseModel):
    group_id: UUID
    group_number: int
    status: GroupStatus
    member_count: int
    first_application_received_at: datetime


class GroupMemberResponse(BaseModel):
    applicant_id: UUID
    full_name: str
    email: str | None = None
    phone: str | None = None
    is_contact: bool
    joined_at: datetime


class GroupDetailResponse(BaseModel):
    group_id: UUID
    group_number: int
    status: GroupStatus
    version: int
    first_application_received_at: datetime
    member_count: int
    members: list[GroupMemberResponse] = Field(default_factory=list)


class CreateGroupRequest(BaseModel):
    applicant_id: UUID
    source_application_id: UUID
    make_contact: bool = True
    reason: str = "manual_create"


class AddGroupMemberRequest(BaseModel):
    applicant_id: UUID
    source_application_id: UUID | None = None
    expected_group_version: int
    reason: str


class SetGroupContactRequest(BaseModel):
    contact_applicant_id: UUID
    expected_group_version: int
    reason: str
