from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from housing_processor.application.handlers.applicants import DeleteApplicantHandler
from housing_processor.domain.applicants.entities import Applicant
from housing_processor.domain.applications.entities import ApplicationRecord
from housing_processor.domain.shared.enums import ApplicationStatus
from housing_processor.domain.shared.errors import ApplicantInGroupError, ResourceNotFoundError
from housing_processor.domain.shared.identifiers import ApplicantId, ApplicationId
from housing_processor.domain.shared.value_objects import PersonName


def _applicant(applicant_id: ApplicantId | None = None) -> Applicant:
    return Applicant(
        id=applicant_id or ApplicantId(uuid4()),
        name=PersonName(first="Pat", last="Sullivan", normalized="pat sullivan"),
        email=None,
        phone=None,
        gpa=None,
        created_at=datetime.now(timezone.utc),
        version=1,
    )


def _application(*, applicant_id: ApplicantId) -> ApplicationRecord:
    return ApplicationRecord(
        id=ApplicationId(uuid4()),
        status=ApplicationStatus.REVIEW_REQUIRED,
        original_filename="00000001-Patrick-Sullivan-Student-App.docx",
        storage_key="sources/x.docx",
        file_hash="abc",
        received_at=datetime.now(timezone.utc),
        source="manual_upload",
        version=3,
        warnings=[f"applicant.upserted:{applicant_id}", "other.warning"],
    )


def _uow_factory(uow: MagicMock):
    factory = MagicMock()
    factory.return_value.__enter__.return_value = uow
    factory.return_value.__exit__.return_value = None
    return factory


def test_delete_applicant_removes_linked_applications() -> None:
    applicant = _applicant()
    application = _application(applicant_id=applicant.id)
    storage = MagicMock()

    uow = MagicMock()
    uow.applicants.get.return_value = applicant
    uow.applicants.is_group_member.return_value = False
    uow.applications.find_with_warning_containing.return_value = (application,)

    DeleteApplicantHandler(_uow_factory(uow), storage).handle(applicant.id)

    uow.applicants.clear_pending_roommate_resolutions.assert_called_once_with(applicant.id)
    uow.applications.delete.assert_called_once_with(application.id)
    uow.applications.save.assert_not_called()
    uow.applicants.delete.assert_called_once_with(applicant.id)
    uow.commit.assert_called_once()
    storage.delete.assert_called_once_with("sources/x.docx")


def test_delete_applicant_in_group_raises() -> None:
    applicant = _applicant()
    uow = MagicMock()
    uow.applicants.get.return_value = applicant
    uow.applicants.is_group_member.return_value = True
    storage = MagicMock()

    with pytest.raises(ApplicantInGroupError):
        DeleteApplicantHandler(_uow_factory(uow), storage).handle(applicant.id)

    uow.applicants.delete.assert_not_called()
    uow.applications.delete.assert_not_called()
    uow.commit.assert_not_called()
    storage.delete.assert_not_called()


def test_delete_applicant_not_found() -> None:
    applicant_id = ApplicantId(uuid4())
    uow = MagicMock()
    uow.applicants.get.side_effect = ResourceNotFoundError(
        f"Applicant {applicant_id} was not found.",
        context={"applicant_id": str(applicant_id)},
    )
    storage = MagicMock()

    with pytest.raises(ResourceNotFoundError):
        DeleteApplicantHandler(_uow_factory(uow), storage).handle(applicant_id)

    uow.applicants.delete.assert_not_called()
    storage.delete.assert_not_called()
