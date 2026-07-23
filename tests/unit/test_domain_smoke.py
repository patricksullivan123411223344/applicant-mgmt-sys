from datetime import datetime, timezone
from uuid import uuid4

import pytest

from housing_processor.domain.groups.entities import GroupMember, HousingGroup
from housing_processor.domain.shared.enums import GroupStatus, MatchMethod
from housing_processor.domain.shared.errors import (
    ContactMustBeGroupMemberError,
    DuplicateGroupMemberError,
)
from housing_processor.domain.shared.identifiers import (
    ApplicantId,
    ApplicationId,
    GroupId,
)
from housing_processor.domain.shared.value_objects import ConfidenceScore
from housing_processor.domain.applications.status_transitions import can_transition
from housing_processor.domain.shared.enums import ApplicationStatus


def test_confidence_score_bounds() -> None:
    assert ConfidenceScore(0.0).value == 0.0
    assert ConfidenceScore(1.0).value == 1.0
    with pytest.raises(ValueError):
        ConfidenceScore(1.1)
    with pytest.raises(ValueError):
        ConfidenceScore(-0.01)


def test_housing_group_add_member_and_set_contact() -> None:
    group = HousingGroup(
        id=GroupId(uuid4()),
        group_number=1,
        status=GroupStatus.INCOMPLETE,
        first_application_received_at=datetime.now(timezone.utc),
    )
    applicant_a = ApplicantId(uuid4())
    applicant_b = ApplicantId(uuid4())
    application_id = ApplicationId(uuid4())
    now = datetime.now(timezone.utc)

    member_a = GroupMember(
        applicant_id=applicant_a,
        is_contact=True,
        match_method=MatchMethod.MANUAL,
        match_confidence=ConfidenceScore(1.0),
        source_application_id=application_id,
        joined_at=now,
    )
    member_b = GroupMember(
        applicant_id=applicant_b,
        is_contact=False,
        match_method=MatchMethod.MANUAL,
        match_confidence=ConfidenceScore(1.0),
        source_application_id=application_id,
        joined_at=now,
    )

    group.add_member(member_a)
    group.add_member(member_b)
    assert len(group.members) == 2

    with pytest.raises(DuplicateGroupMemberError):
        group.add_member(member_a)

    group.set_contact(applicant_b)
    assert group.members[0].is_contact is False
    assert group.members[1].is_contact is True

    with pytest.raises(ContactMustBeGroupMemberError):
        group.set_contact(ApplicantId(uuid4()))


def test_application_status_transitions() -> None:
    assert can_transition(ApplicationStatus.RECEIVED, ApplicationStatus.EXTRACTING)
    assert can_transition(ApplicationStatus.RECEIVED, ApplicationStatus.DUPLICATE)
    assert not can_transition(ApplicationStatus.RECEIVED, ApplicationStatus.MATCHED)
    assert can_transition(ApplicationStatus.REVIEW_REQUIRED, ApplicationStatus.MATCHED)
    assert can_transition(ApplicationStatus.REVIEW_REQUIRED, ApplicationStatus.EXTRACTING)
    assert can_transition(ApplicationStatus.MATCHED, ApplicationStatus.EXTRACTING)
    assert can_transition(ApplicationStatus.FAILED, ApplicationStatus.EXTRACTING)
