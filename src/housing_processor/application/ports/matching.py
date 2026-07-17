from typing import Protocol

from housing_processor.domain.applicants.entities import ApplicantCandidate
from housing_processor.domain.applications.validation import ValidatedApplicationData
from housing_processor.domain.groups.entities import HousingGroup
from housing_processor.domain.matching.decisions import GroupMatchDecision
from housing_processor.domain.matching.resolution import ApplicantResolution


class ApplicantIdentityResolver(Protocol):
    def resolve(self, candidate: ApplicantCandidate) -> ApplicantResolution: ...


class GroupMatcher(Protocol):
    def match(
        self,
        application: ValidatedApplicationData,
        applicant: ApplicantResolution,
        candidate_groups: tuple[HousingGroup, ...],
    ) -> GroupMatchDecision: ...
