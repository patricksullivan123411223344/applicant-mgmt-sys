from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from housing_processor.domain.shared.identifiers import ApplicantId
from housing_processor.domain.shared.value_objects import EmailAddress, PersonName, PhoneNumber


@dataclass(slots=True)
class Applicant:
    id: ApplicantId
    name: PersonName
    email: EmailAddress | None
    phone: PhoneNumber | None
    gpa: Decimal | None
    created_at: datetime
    version: int = 1


@dataclass(frozen=True, slots=True)
class ApplicantCandidate:
    """Normalized applicant data prior to identity resolution / persistence."""

    name: PersonName
    email: EmailAddress | None
    phone: PhoneNumber | None
    gpa: Decimal | None
