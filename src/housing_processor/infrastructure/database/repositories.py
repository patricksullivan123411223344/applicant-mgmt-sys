from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

from housing_processor.domain.applicants.entities import Applicant
from housing_processor.domain.applications.entities import ApplicationRecord
from housing_processor.domain.audit.events import AuditEvent
from housing_processor.domain.groups.entities import HousingGroup
from housing_processor.domain.reviews.entities import ReviewItem
from housing_processor.domain.shared.enums import ApplicationStatus, GroupStatus
from housing_processor.domain.shared.errors import ResourceNotFoundError
from housing_processor.domain.shared.identifiers import (
    ApplicantId,
    ApplicationId,
    GroupId,
    ReviewItemId,
)
from housing_processor.infrastructure.database.mappers import (
    applicant_to_domain,
    application_to_domain,
    application_to_model,
    audit_to_model,
    group_to_domain,
    review_to_domain,
)
from housing_processor.infrastructure.database.models.applicants import ApplicantModel
from housing_processor.infrastructure.database.models.applications import ApplicationModel
from housing_processor.infrastructure.database.models.groups import (
    GroupMemberModel,
    GroupModel,
    GroupNumberSequenceModel,
)
from housing_processor.infrastructure.database.models.reviews import ReviewItemModel
from housing_processor.application.ports.repositories import GroupCandidateQuery


class SqlAlchemyApplicationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, application_id: ApplicationId) -> ApplicationRecord:
        model = self._session.get(ApplicationModel, UUID(str(application_id)))
        if model is None:
            raise ResourceNotFoundError(
                f"Application {application_id} was not found.",
                context={"application_id": str(application_id)},
            )
        return application_to_domain(model)

    def find_by_file_hash(self, file_hash: str) -> ApplicationRecord | None:
        stmt = select(ApplicationModel).where(ApplicationModel.file_hash == file_hash)
        model = self._session.scalars(stmt).first()
        return application_to_domain(model) if model else None

    def list(
        self,
        *,
        status: ApplicationStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[tuple[ApplicationRecord, ...], int]:
        filters = []
        if status is not None:
            filters.append(ApplicationModel.status == status.value)
        count_stmt = select(func.count()).select_from(ApplicationModel)
        list_stmt = select(ApplicationModel).order_by(ApplicationModel.received_at.desc())
        if filters:
            count_stmt = count_stmt.where(*filters)
            list_stmt = list_stmt.where(*filters)
        total = int(self._session.scalar(count_stmt) or 0)
        models = list(self._session.scalars(list_stmt.limit(limit).offset(offset)).all())
        return tuple(application_to_domain(m) for m in models), total

    def find_with_warning_containing(self, needle: str) -> tuple[ApplicationRecord, ...]:
        stmt = select(ApplicationModel).where(ApplicationModel.warnings_json.contains(needle))
        return tuple(application_to_domain(m) for m in self._session.scalars(stmt).all())

    def add(self, application: ApplicationRecord) -> None:
        self._session.add(application_to_model(application))

    def save(self, application: ApplicationRecord) -> None:
        existing = self._session.get(ApplicationModel, UUID(str(application.id)))
        if existing is None:
            self.add(application)
            return
        application_to_model(application, existing=existing)

    def delete(self, application_id: ApplicationId) -> None:
        from housing_processor.infrastructure.database.models.pending_roommates import (
            PendingRoommateReferenceModel,
        )
        from housing_processor.infrastructure.database.models.reviews import ReviewItemModel

        app_uuid = UUID(str(application_id))
        model = self._session.get(ApplicationModel, app_uuid)
        if model is None:
            raise ResourceNotFoundError(
                f"Application {application_id} was not found.",
                context={"application_id": str(application_id)},
            )

        # Dependents that reference applications (pending has a real FK).
        self._session.execute(
            PendingRoommateReferenceModel.__table__.delete().where(
                PendingRoommateReferenceModel.source_application_id == app_uuid
            )
        )
        self._session.execute(
            ReviewItemModel.__table__.delete().where(ReviewItemModel.application_id == app_uuid)
        )
        # Clear duplicate pointers at this application.
        self._session.execute(
            update(ApplicationModel)
            .where(ApplicationModel.duplicate_of_application_id == app_uuid)
            .values(duplicate_of_application_id=None)
        )
        self._session.delete(model)


class SqlAlchemyApplicantRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, applicant_id: ApplicantId) -> Applicant:
        model = self._session.get(ApplicantModel, UUID(str(applicant_id)))
        if model is None:
            raise ResourceNotFoundError(
                f"Applicant {applicant_id} was not found.",
                context={"applicant_id": str(applicant_id)},
            )
        return applicant_to_domain(model)

    def find_by_email(self, normalized_email: str) -> tuple[Applicant, ...]:
        stmt = select(ApplicantModel).where(ApplicantModel.email_normalized == normalized_email)
        return tuple(applicant_to_domain(m) for m in self._session.scalars(stmt).all())

    def find_by_phone(self, e164_phone: str) -> tuple[Applicant, ...]:
        stmt = select(ApplicantModel).where(ApplicantModel.phone_e164 == e164_phone)
        return tuple(applicant_to_domain(m) for m in self._session.scalars(stmt).all())

    def search_by_name(self, normalized_name: str) -> tuple[Applicant, ...]:
        stmt = select(ApplicantModel).where(ApplicantModel.normalized_name == normalized_name)
        return tuple(applicant_to_domain(m) for m in self._session.scalars(stmt).all())

    def add(self, applicant: Applicant) -> None:
        now = datetime.now(timezone.utc)
        self._session.add(
            ApplicantModel(
                id=UUID(str(applicant.id)),
                first_name=applicant.name.first,
                last_name=applicant.name.last,
                normalized_name=applicant.name.normalized,
                email_original=applicant.email.original if applicant.email else None,
                email_normalized=applicant.email.normalized if applicant.email else None,
                phone_original=applicant.phone.original if applicant.phone else None,
                phone_e164=applicant.phone.e164 if applicant.phone else None,
                gpa=applicant.gpa,
                version=applicant.version,
                created_at=now,
                updated_at=now,
            )
        )

    def save(self, applicant: Applicant) -> None:
        model = self._session.get(ApplicantModel, UUID(str(applicant.id)))
        if model is None:
            self.add(applicant)
            return
        model.first_name = applicant.name.first
        model.last_name = applicant.name.last
        model.normalized_name = applicant.name.normalized
        model.email_original = applicant.email.original if applicant.email else None
        model.email_normalized = applicant.email.normalized if applicant.email else None
        model.phone_original = applicant.phone.original if applicant.phone else None
        model.phone_e164 = applicant.phone.e164 if applicant.phone else None
        model.gpa = applicant.gpa
        model.version = applicant.version
        model.updated_at = datetime.now(timezone.utc)

    def delete(self, applicant_id: ApplicantId) -> None:
        model = self._session.get(ApplicantModel, UUID(str(applicant_id)))
        if model is None:
            raise ResourceNotFoundError(
                f"Applicant {applicant_id} was not found.",
                context={"applicant_id": str(applicant_id)},
            )
        self._session.delete(model)

    def is_group_member(self, applicant_id: ApplicantId) -> bool:
        stmt = (
            select(func.count())
            .select_from(GroupMemberModel)
            .where(GroupMemberModel.applicant_id == UUID(str(applicant_id)))
        )
        return int(self._session.scalar(stmt) or 0) > 0

    def clear_pending_roommate_resolutions(self, applicant_id: ApplicantId) -> None:
        from housing_processor.infrastructure.database.models.pending_roommates import (
            PendingRoommateReferenceModel,
        )

        self._session.execute(
            update(PendingRoommateReferenceModel)
            .where(
                PendingRoommateReferenceModel.resolved_applicant_id
                == UUID(str(applicant_id))
            )
            .values(resolved_applicant_id=None)
        )


class SqlAlchemyGroupRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, group_id: GroupId, *, for_update: bool = False) -> HousingGroup:
        stmt = select(GroupModel).where(GroupModel.id == UUID(str(group_id)))
        if for_update:
            stmt = stmt.with_for_update()
        model = self._session.scalars(stmt).first()
        if model is None:
            raise ResourceNotFoundError(
                f"Group {group_id} was not found.",
                context={"group_id": str(group_id)},
            )
        members = self._members_for(model.id)
        return group_to_domain(model, members)

    def _members_for(self, group_id: UUID) -> list[GroupMemberModel]:
        return list(
            self._session.scalars(
                select(GroupMemberModel).where(GroupMemberModel.group_id == group_id)
            ).all()
        )

    def find_by_group_number(self, group_number: int) -> HousingGroup | None:
        model = self._session.scalars(
            select(GroupModel).where(GroupModel.group_number == group_number)
        ).first()
        if model is None:
            return None
        return group_to_domain(model, self._members_for(model.id))

    def list(
        self,
        *,
        group_number: int | None = None,
        status: GroupStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[tuple[HousingGroup, ...], int]:
        filters = []
        if group_number is not None:
            filters.append(GroupModel.group_number == group_number)
        if status is not None:
            filters.append(GroupModel.status == status.value)
        count_stmt = select(func.count()).select_from(GroupModel)
        list_stmt = select(GroupModel).order_by(GroupModel.group_number.asc())
        if filters:
            count_stmt = count_stmt.where(*filters)
            list_stmt = list_stmt.where(*filters)
        total = int(self._session.scalar(count_stmt) or 0)
        models = list(self._session.scalars(list_stmt.limit(limit).offset(offset)).all())
        return (
            tuple(group_to_domain(m, self._members_for(m.id)) for m in models),
            total,
        )

    def find_candidates(self, query: GroupCandidateQuery) -> tuple[HousingGroup, ...]:
        _ = query
        groups = list(self._session.scalars(select(GroupModel)).all())
        return tuple(group_to_domain(m, self._members_for(m.id)) for m in groups)

    def add(self, group: HousingGroup) -> None:
        now = datetime.now(timezone.utc)
        self._session.add(
            GroupModel(
                id=UUID(str(group.id)),
                group_number=group.group_number,
                status=group.status.value,
                first_application_received_at=group.first_application_received_at,
                version=group.version,
                created_at=now,
                updated_at=now,
            )
        )
        # Ensure the parent row exists before FK inserts into group_members.
        self._session.flush()
        for member in group.members:
            self._session.add(
                GroupMemberModel(
                    id=uuid4(),
                    group_id=UUID(str(group.id)),
                    applicant_id=UUID(str(member.applicant_id)),
                    is_contact=member.is_contact,
                    match_method=member.match_method.value,
                    match_confidence=member.match_confidence.value,
                    source_application_id=UUID(str(member.source_application_id)),
                    joined_at=member.joined_at,
                )
            )

    def save(self, group: HousingGroup) -> None:
        model = self._session.get(GroupModel, UUID(str(group.id)))
        if model is None:
            self.add(group)
            return
        model.status = group.status.value
        model.version = group.version
        model.updated_at = datetime.now(timezone.utc)
        existing = {
            m.applicant_id
            for m in self._session.scalars(
                select(GroupMemberModel).where(GroupMemberModel.group_id == model.id)
            ).all()
        }
        for member in group.members:
            applicant_uuid = UUID(str(member.applicant_id))
            if applicant_uuid in existing:
                row = self._session.scalars(
                    select(GroupMemberModel).where(
                        GroupMemberModel.group_id == model.id,
                        GroupMemberModel.applicant_id == applicant_uuid,
                    )
                ).first()
                if row is not None:
                    row.is_contact = member.is_contact
                continue
            self._session.add(
                GroupMemberModel(
                    id=uuid4(),
                    group_id=model.id,
                    applicant_id=applicant_uuid,
                    is_contact=member.is_contact,
                    match_method=member.match_method.value,
                    match_confidence=member.match_confidence.value,
                    source_application_id=UUID(str(member.source_application_id)),
                    joined_at=member.joined_at,
                )
            )
        # Sync contact flags for existing members
        for member in group.members:
            applicant_uuid = UUID(str(member.applicant_id))
            if applicant_uuid not in existing:
                continue
            row = self._session.scalars(
                select(GroupMemberModel).where(
                    GroupMemberModel.group_id == model.id,
                    GroupMemberModel.applicant_id == applicant_uuid,
                )
            ).first()
            if row is not None:
                row.is_contact = member.is_contact

    def allocate_group_number(self) -> int:
        """Atomically allocate the next permanent group number."""
        bind = self._session.get_bind()
        if bind is not None and bind.dialect.name == "postgresql":
            # SYSTEM_ARCHITECTURE §21 — database sequence.
            result = self._session.execute(text("SELECT nextval('group_number_seq')"))
            return int(result.scalar_one())

        row = self._session.scalars(
            select(GroupNumberSequenceModel).where(GroupNumberSequenceModel.id == 1).with_for_update()
        ).first()
        if row is None:
            row = GroupNumberSequenceModel(id=1, next_value=1)
            self._session.add(row)
            self._session.flush()
        allocated = row.next_value
        self._session.execute(
            update(GroupNumberSequenceModel)
            .where(GroupNumberSequenceModel.id == 1)
            .values(next_value=allocated + 1)
        )
        return allocated


class SqlAlchemyReviewRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, review_id: ReviewItemId, *, for_update: bool = False) -> ReviewItem:
        stmt = select(ReviewItemModel).where(ReviewItemModel.id == UUID(str(review_id)))
        if for_update:
            stmt = stmt.with_for_update()
        model = self._session.scalars(stmt).first()
        if model is None:
            raise ResourceNotFoundError(
                f"Review item {review_id} was not found.",
                context={"review_item_id": str(review_id)},
            )
        return review_to_domain(model)

    def add(self, review: ReviewItem) -> None:
        self._session.add(
            ReviewItemModel(
                id=UUID(str(review.id)),
                application_id=UUID(str(review.application_id)),
                status=review.status.value,
                reason_codes_json=json.dumps(list(review.reason_codes)),
                suggested_group_id=(
                    UUID(str(review.suggested_group_id)) if review.suggested_group_id else None
                ),
                evidence_summary_json=json.dumps(review.evidence_summary),
                version=review.version,
                created_at=review.created_at,
                resolved_at=review.resolved_at,
                resolved_by=review.resolved_by,
                resolution_notes=review.resolution_notes,
            )
        )

    def save(self, review: ReviewItem) -> None:
        model = self._session.get(ReviewItemModel, UUID(str(review.id)))
        if model is None:
            self.add(review)
            return
        model.status = review.status.value
        model.reason_codes_json = json.dumps(list(review.reason_codes))
        model.suggested_group_id = (
            UUID(str(review.suggested_group_id)) if review.suggested_group_id else None
        )
        model.evidence_summary_json = json.dumps(review.evidence_summary)
        model.version = review.version
        model.resolved_at = review.resolved_at
        model.resolved_by = review.resolved_by
        model.resolution_notes = review.resolution_notes


class SqlAlchemyAuditRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, event: AuditEvent) -> None:
        self._session.add(audit_to_model(event))
