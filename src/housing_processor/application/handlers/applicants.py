"""Correct / upsert applicant fields for an application (manual ops)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from uuid import uuid4

from housing_processor.application.ports.repositories import UnitOfWorkFactory
from housing_processor.application.ports.storage import FileStorage
from housing_processor.application.ports.support import Clock
from housing_processor.domain.applicants.entities import Applicant
from housing_processor.domain.shared.errors import (
    ApplicantInGroupError,
    DomainError,
    VersionConflictError,
)
from housing_processor.domain.shared.identifiers import ApplicantId, ApplicationId
from housing_processor.domain.shared.value_objects import EmailAddress, PersonName, PhoneNumber
from housing_processor.infrastructure.docx import NA


def _split_name(full_name: str) -> PersonName:
    cleaned = full_name.strip()
    parts = cleaned.split()
    first = parts[0] if parts else "Unknown"
    last = " ".join(parts[1:]) if len(parts) > 1 else "Applicant"
    return PersonName(first=first, last=last, normalized=f"{first} {last}".casefold())


def _email(raw: str | None) -> EmailAddress | None:
    if raw is None or not raw.strip() or raw.strip().upper() == NA:
        return None
    original = raw.strip()
    return EmailAddress(original=original, normalized=original.casefold())


def _phone(raw: str | None) -> PhoneNumber | None:
    if raw is None or not raw.strip() or raw.strip().upper() == NA:
        return None
    original = raw.strip()
    digits = "".join(ch for ch in original if ch.isdigit() or ch == "+")
    e164 = digits if digits.startswith("+") else f"+1{digits}" if len(digits) == 10 else digits
    if not e164:
        return None
    return PhoneNumber(original=original, e164=e164)


class UpsertApplicationApplicantHandler:
    """Create or update the primary applicant linked via processing result storage.

    v1: stores applicant and records linkage via re-fetch after process; also
    accepts explicit applicant fields from the application detail form.
    """

    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def handle(
        self,
        *,
        application_id: ApplicationId,
        expected_version: int,
        full_name: str,
        email: str | None,
        phone: str | None,
        gpa: str | None,
        applicant_id: ApplicantId | None = None,
    ) -> Applicant:
        if not full_name.strip() or full_name.strip().upper() == NA:
            raise DomainError(
                "A real applicant name is required.",
                code="applicant.name_required",
            )
        gpa_val: Decimal | None = None
        if gpa and gpa.strip() and gpa.strip().upper() != NA:
            try:
                gpa_val = Decimal(gpa.strip())
            except (InvalidOperation, ValueError) as exc:
                raise DomainError("GPA must be numeric or N/A.", code="applicant.gpa_invalid") from exc

        with self._uow_factory() as uow:
            application = uow.applications.get(application_id)
            if application.version != expected_version:
                raise VersionConflictError(
                    "Application was modified by another request.",
                    context={"expected": expected_version, "actual": application.version},
                )

            name = _split_name(full_name)
            now = self._clock.now()
            if applicant_id is not None:
                applicant = uow.applicants.get(applicant_id)
                applicant.name = name
                applicant.email = _email(email)
                applicant.phone = _phone(phone)
                applicant.gpa = gpa_val
                applicant.version += 1
                uow.applicants.save(applicant)
            else:
                applicant_id = ApplicantId(uuid4())
                applicant = Applicant(
                    id=applicant_id,
                    name=name,
                    email=_email(email),
                    phone=_phone(phone),
                    gpa=gpa_val,
                    created_at=now,
                    version=1,
                )
                uow.applicants.add(applicant)

            application.version += 1
            warning = f"applicant.upserted:{applicant_id}"
            if warning not in application.warnings:
                application.warnings = list(application.warnings) + [warning]
            uow.applications.save(application)
            uow.commit()
            return applicant


class DeleteApplicantHandler:
    """Hard-delete an applicant and any applications linked to them.

    Refuses if the applicant is still a group member. Linked applications
    (via ``applicant.upserted:{id}``) are removed from the Applications list
    along with related review/pending rows and stored Word files.
    """

    def __init__(self, uow_factory: UnitOfWorkFactory, storage: FileStorage) -> None:
        self._uow_factory = uow_factory
        self._storage = storage

    def handle(self, applicant_id: ApplicantId) -> None:
        with self._uow_factory() as uow:
            uow.applicants.get(applicant_id)
            if uow.applicants.is_group_member(applicant_id):
                raise ApplicantInGroupError(applicant_id)

            uow.applicants.clear_pending_roommate_resolutions(applicant_id)

            tag = f"applicant.upserted:{applicant_id}"
            linked = list(uow.applications.find_with_warning_containing(tag))
            storage_keys = [app.storage_key for app in linked if app.storage_key]

            for application in linked:
                uow.applications.delete(application.id)

            uow.applicants.delete(applicant_id)
            uow.commit()

        for key in storage_keys:
            try:
                self._storage.delete(key)
            except OSError:
                continue
