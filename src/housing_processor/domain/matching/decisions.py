from dataclasses import dataclass

from housing_processor.domain.shared.enums import MatchDecisionType
from housing_processor.domain.shared.identifiers import ApplicantId, ApplicationId, GroupId
from housing_processor.domain.shared.value_objects import ConfidenceScore


@dataclass(frozen=True, slots=True)
class MatchEvidence:
    code: str
    description: str
    weight: int
    source_application_id: ApplicationId | None = None
    related_applicant_id: ApplicantId | None = None


@dataclass(frozen=True, slots=True)
class GroupCandidate:
    group_id: GroupId
    group_number: int
    score: int
    evidence: tuple[MatchEvidence, ...]
    hard_conflicts: tuple[MatchEvidence, ...]


@dataclass(frozen=True, slots=True)
class GroupMatchDecision:
    decision: MatchDecisionType
    selected_group_id: GroupId | None
    confidence: ConfidenceScore
    candidates: tuple[GroupCandidate, ...]
    reason_codes: tuple[str, ...]
    matcher_version: str
