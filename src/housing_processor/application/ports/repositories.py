from typing import Protocol

from housing_processor.domain.applicants.entities import Applicant
from housing_processor.domain.applications.entities import ApplicationRecord
from housing_processor.domain.audit.events import AuditEvent
from housing_processor.domain.groups.entities import HousingGroup
from housing_processor.domain.reviews.entities import ReviewItem
from housing_processor.domain.shared.enums import ApplicationStatus, GroupStatus
from housing_processor.domain.shared.identifiers import (
    ApplicantId,
    ApplicationId,
    GroupId,
    ReviewItemId,
)


class ApplicationRepository(Protocol):
    def get(self, application_id: ApplicationId) -> ApplicationRecord: ...

    def find_by_file_hash(self, file_hash: str) -> ApplicationRecord | None: ...

    def list(
        self,
        *,
        status: ApplicationStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[tuple[ApplicationRecord, ...], int]: ...

    def add(self, application: ApplicationRecord) -> None: ...

    def save(self, application: ApplicationRecord) -> None: ...


class ApplicantRepository(Protocol):
    def get(self, applicant_id: ApplicantId) -> Applicant: ...

    def find_by_email(self, normalized_email: str) -> tuple[Applicant, ...]: ...

    def find_by_phone(self, e164_phone: str) -> tuple[Applicant, ...]: ...

    def search_by_name(self, normalized_name: str) -> tuple[Applicant, ...]: ...

    def add(self, applicant: Applicant) -> None: ...

    def save(self, applicant: Applicant) -> None: ...


class GroupCandidateQuery:
    """Opaque query object for loading group match candidates."""

    def __init__(self, **criteria: object) -> None:
        self.criteria = criteria


class GroupRepository(Protocol):
    def get(self, group_id: GroupId, *, for_update: bool = False) -> HousingGroup: ...

    def find_by_group_number(self, group_number: int) -> HousingGroup | None: ...

    def list(
        self,
        *,
        group_number: int | None = None,
        status: GroupStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[tuple[HousingGroup, ...], int]: ...

    def find_candidates(self, query: GroupCandidateQuery) -> tuple[HousingGroup, ...]: ...

    def add(self, group: HousingGroup) -> None: ...

    def save(self, group: HousingGroup) -> None: ...

    def allocate_group_number(self) -> int: ...


class ReviewRepository(Protocol):
    def get(self, review_id: ReviewItemId, *, for_update: bool = False) -> ReviewItem: ...

    def add(self, review: ReviewItem) -> None: ...

    def save(self, review: ReviewItem) -> None: ...


class AuditRepository(Protocol):
    def add(self, event: AuditEvent) -> None: ...


class UnitOfWork(Protocol):
    applications: ApplicationRepository
    applicants: ApplicantRepository
    groups: GroupRepository
    reviews: ReviewRepository
    audits: AuditRepository

    def __enter__(self) -> "UnitOfWork": ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> UnitOfWork: ...
