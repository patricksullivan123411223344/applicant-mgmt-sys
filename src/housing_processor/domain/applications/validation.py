"""Validation outcomes for extracted application data."""

from dataclasses import dataclass
from datetime import date

from housing_processor.domain.applicants.entities import ApplicantCandidate
from housing_processor.domain.properties.entities import HousePreference
from housing_processor.domain.shared.value_objects import PersonName


@dataclass(frozen=True, slots=True)
class PersonReference:
    name: PersonName
    email_raw: str | None = None
    phone_raw: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    field_path: str
    severity: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidatedApplicationData:
    applicant: ApplicantCandidate
    roommates: tuple[PersonReference, ...]
    contact_person: PersonReference | None
    house_preferences: tuple[HousePreference, ...]
    expected_group_size: int | None
    application_date: date | None
    issues: tuple[ValidationIssue, ...]
