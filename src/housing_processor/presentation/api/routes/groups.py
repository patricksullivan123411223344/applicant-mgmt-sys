from uuid import UUID

from fastapi import APIRouter, Depends, status

from housing_processor.bootstrap import AppContainer
from housing_processor.domain.shared.enums import GroupStatus
from housing_processor.domain.shared.errors import ResourceNotFoundError
from housing_processor.domain.shared.identifiers import GroupId
from housing_processor.presentation.api.contracts.common import PageMeta, PaginatedResponse
from housing_processor.presentation.api.contracts.groups import (
    AddGroupMemberRequest,
    GroupDetailResponse,
    GroupMemberResponse,
    GroupSummaryResponse,
    SetGroupContactRequest,
)
from housing_processor.presentation.api.dependencies import get_actor_context, get_app_container

router = APIRouter(
    prefix="/groups",
    tags=["groups"],
    dependencies=[Depends(get_actor_context)],
)


def _summary_from_group(group) -> GroupSummaryResponse:  # type: ignore[no-untyped-def]
    return GroupSummaryResponse(
        group_id=UUID(str(group.id)),
        group_number=group.group_number,
        status=group.status,
        member_count=len(group.members),
        first_application_received_at=group.first_application_received_at,
    )


def _detail_from_group(group, uow) -> GroupDetailResponse:  # type: ignore[no-untyped-def]
    members: list[GroupMemberResponse] = []
    for member in group.members:
        applicant = uow.applicants.get(member.applicant_id)
        full_name = f"{applicant.name.first} {applicant.name.last}".strip()
        members.append(
            GroupMemberResponse(
                applicant_id=UUID(str(member.applicant_id)),
                full_name=full_name,
                email=applicant.email.original if applicant.email else None,
                phone=applicant.phone.original if applicant.phone else None,
                is_contact=member.is_contact,
                joined_at=member.joined_at,
            )
        )
    members.sort(key=lambda m: (not m.is_contact, m.full_name.lower()))
    return GroupDetailResponse(
        group_id=UUID(str(group.id)),
        group_number=group.group_number,
        status=group.status,
        version=group.version,
        first_application_received_at=group.first_application_received_at,
        member_count=len(members),
        members=members,
    )


@router.get("", response_model=PaginatedResponse[GroupSummaryResponse])
def list_groups(
    limit: int = 50,
    offset: int = 0,
    group_number: int | None = None,
    status_filter: GroupStatus | None = None,
    container: AppContainer = Depends(get_app_container),
) -> PaginatedResponse[GroupSummaryResponse]:
    with container.uow_factory() as uow:
        groups, total = uow.groups.list(
            group_number=group_number,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        items = [_summary_from_group(g) for g in groups]
        return PaginatedResponse(
            items=items,
            page=PageMeta(limit=limit, offset=offset, total=total),
        )


@router.get("/by-number/{group_number}", response_model=GroupDetailResponse)
def get_group_by_number(
    group_number: int,
    container: AppContainer = Depends(get_app_container),
) -> GroupDetailResponse:
    with container.uow_factory() as uow:
        group = uow.groups.find_by_group_number(group_number)
        if group is None:
            raise ResourceNotFoundError(
                f"Group number {group_number} was not found.",
                context={"group_number": group_number},
            )
        return _detail_from_group(group, uow)


@router.get("/{group_id}", response_model=GroupDetailResponse)
def get_group(
    group_id: UUID,
    container: AppContainer = Depends(get_app_container),
) -> GroupDetailResponse:
    with container.uow_factory() as uow:
        group = uow.groups.get(GroupId(group_id))
        return _detail_from_group(group, uow)


@router.post("", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def create_group() -> dict[str, str]:
    return {"detail": "Manual group creation is not implemented in Phase 1 scaffold."}


@router.post("/{group_id}/members", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def add_member(group_id: UUID, body: AddGroupMemberRequest) -> dict[str, str]:
    _ = group_id, body
    return {"detail": "Add group member is not implemented in Phase 1 scaffold."}


@router.put("/{group_id}/contact", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def set_contact(group_id: UUID, body: SetGroupContactRequest) -> dict[str, str]:
    _ = group_id, body
    return {"detail": "Set group contact is not implemented in Phase 1 scaffold."}
