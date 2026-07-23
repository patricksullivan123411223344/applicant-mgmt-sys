"""Manual group create / attach / set contact."""

from __future__ import annotations

from uuid import UUID, uuid4

from housing_processor.application.ports.repositories import UnitOfWorkFactory
from housing_processor.application.ports.support import Clock
from housing_processor.domain.applications.status_transitions import assert_can_transition
from housing_processor.domain.groups.entities import GroupMember, HousingGroup
from housing_processor.domain.shared.enums import ApplicationStatus, GroupStatus, MatchMethod
from housing_processor.domain.shared.errors import DomainError, VersionConflictError
from housing_processor.domain.shared.identifiers import ApplicantId, ApplicationId, GroupId
from housing_processor.domain.shared.value_objects import ConfidenceScore


class CreateGroupHandler:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def handle(
        self,
        *,
        applicant_id: ApplicantId,
        source_application_id: ApplicationId | None,
        make_contact: bool = True,
    ) -> HousingGroup:
        with self._uow_factory() as uow:
            applicant = uow.applicants.get(applicant_id)
            if applicant.name.first.casefold() in {"unknown", "n/a"} and applicant.name.last.casefold() in {
                "applicant",
                "n/a",
            }:
                raise DomainError(
                    "Applicant needs a real name before creating a group.",
                    code="group.applicant_name_required",
                )

            now = self._clock.now()
            group_number = uow.groups.allocate_group_number()
            group_id = GroupId(uuid4())
            source_app = source_application_id
            if source_app is None:
                raise DomainError(
                    "source_application_id is required when creating a group.",
                    code="group.source_application_required",
                )

            member = GroupMember(
                applicant_id=applicant_id,
                is_contact=make_contact,
                match_method=MatchMethod.MANUAL,
                match_confidence=ConfidenceScore(1.0),
                source_application_id=source_app,
                joined_at=now,
            )
            group = HousingGroup(
                id=group_id,
                group_number=group_number,
                status=GroupStatus.INCOMPLETE,
                first_application_received_at=now,
                members=[member],
                version=1,
            )
            uow.groups.add(group)

            application = uow.applications.get(source_app)
            if application.status in {
                ApplicationStatus.REVIEW_REQUIRED,
                ApplicationStatus.MATCHING,
                ApplicationStatus.EXTRACTED,
                ApplicationStatus.RECEIVED,
            }:
                try:
                    assert_can_transition(
                        application.id,
                        application.status,
                        ApplicationStatus.MATCHED,
                    )
                except DomainError:
                    pass
                else:
                    application.status = ApplicationStatus.MATCHED
            application.group_id = group_id
            uow.applications.save(application)
            uow.commit()
            return group


class AddGroupMemberHandler:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def handle(
        self,
        *,
        group_id: GroupId,
        applicant_id: ApplicantId,
        source_application_id: ApplicationId | None,
        expected_group_version: int,
    ) -> HousingGroup:
        with self._uow_factory() as uow:
            group = uow.groups.get(group_id, for_update=True)
            if group.version != expected_group_version:
                raise VersionConflictError(
                    "Group was modified by another request.",
                    context={"expected": expected_group_version, "actual": group.version},
                )
            _ = uow.applicants.get(applicant_id)
            source_app = source_application_id
            if source_app is None:
                raise DomainError(
                    "source_application_id is required when adding a member.",
                    code="group.source_application_required",
                )
            group.add_member(
                GroupMember(
                    applicant_id=applicant_id,
                    is_contact=False,
                    match_method=MatchMethod.MANUAL,
                    match_confidence=ConfidenceScore(1.0),
                    source_application_id=source_app,
                    joined_at=self._clock.now(),
                )
            )
            group.version += 1
            uow.groups.save(group)

            application = uow.applications.get(source_app)
            application.group_id = group_id
            if application.status == ApplicationStatus.REVIEW_REQUIRED:
                try:
                    assert_can_transition(
                        application.id,
                        application.status,
                        ApplicationStatus.MATCHED,
                    )
                    application.status = ApplicationStatus.MATCHED
                except DomainError:
                    pass
            uow.applications.save(application)
            uow.commit()
            return group


class SetGroupContactHandler:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def handle(
        self,
        *,
        group_id: GroupId,
        contact_applicant_id: ApplicantId,
        expected_group_version: int,
    ) -> HousingGroup:
        with self._uow_factory() as uow:
            group = uow.groups.get(group_id, for_update=True)
            if group.version != expected_group_version:
                raise VersionConflictError(
                    "Group was modified by another request.",
                    context={"expected": expected_group_version, "actual": group.version},
                )
            group.set_contact(contact_applicant_id)
            group.version += 1
            uow.groups.save(group)
            uow.commit()
            return group
