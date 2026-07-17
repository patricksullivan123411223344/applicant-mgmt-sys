from housing_processor.application.contracts.extraction import (
    ExtractedApplicationContract,
    RawDocumentContent,
)
from housing_processor.domain.applicants.entities import ApplicantCandidate
from housing_processor.domain.applications.validation import ValidatedApplicationData
from housing_processor.domain.groups.entities import HousingGroup
from housing_processor.domain.matching.decisions import GroupMatchDecision
from housing_processor.domain.matching.resolution import ApplicantResolution
from housing_processor.domain.shared.enums import MatchDecisionType
from housing_processor.domain.shared.value_objects import ConfidenceScore


MATCHER_VERSION = "review-stub-0.1.0"


class NoOpLlmStructuredExtractor:
    """LLM adapter stub used when llm_enabled is false."""

    def extract(
        self,
        document: RawDocumentContent,
        deterministic_result: ExtractedApplicationContract,
    ) -> ExtractedApplicationContract:
        _ = document
        return deterministic_result


class StubIdentityResolver:
    """Phase 1: does not auto-match identities; leaves applicant unset for review."""

    def resolve(self, candidate: ApplicantCandidate) -> ApplicantResolution:
        return ApplicantResolution(
            applicant_id=None,
            is_new=True,
            requires_review=True,
            matched_applicant=None,
            evidence=(),
            reason_codes=("identity.deferred_phase1",),
        )


class ReviewRequiredGroupMatcher:
    """Phase 1: always returns REVIEW_REQUIRED so staff select groups manually."""

    def match(
        self,
        application: ValidatedApplicationData,
        applicant: ApplicantResolution,
        candidate_groups: tuple[HousingGroup, ...],
    ) -> GroupMatchDecision:
        _ = application, applicant, candidate_groups
        return GroupMatchDecision(
            decision=MatchDecisionType.REVIEW_REQUIRED,
            selected_group_id=None,
            confidence=ConfidenceScore(0.0),
            candidates=(),
            reason_codes=("match.manual_review_phase1",),
            matcher_version=MATCHER_VERSION,
        )
