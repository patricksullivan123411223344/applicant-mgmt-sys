from dataclasses import dataclass

from housing_processor.domain.applicants.entities import Applicant
from housing_processor.domain.matching.decisions import MatchEvidence
from housing_processor.domain.shared.identifiers import ApplicantId


@dataclass(frozen=True, slots=True)
class ApplicantResolution:
    """Result of identity resolution: existing applicant, new candidate, or review."""

    applicant_id: ApplicantId | None
    is_new: bool
    requires_review: bool
    matched_applicant: Applicant | None
    evidence: tuple[MatchEvidence, ...]
    reason_codes: tuple[str, ...]
