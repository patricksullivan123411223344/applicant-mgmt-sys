"""Map between SQLAlchemy models and domain entities."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from housing_processor.domain.applicants.entities import Applicant
from housing_processor.domain.applications.entities import ApplicationRecord
from housing_processor.domain.audit.events import AuditEvent
from housing_processor.domain.groups.entities import GroupMember, HousingGroup
from housing_processor.domain.reviews.entities import ReviewItem
from housing_processor.domain.shared.enums import (
    ApplicationStatus,
    GroupStatus,
    MatchMethod,
    ReviewStatus,
)
from housing_processor.domain.shared.identifiers import (
    ApplicantId,
    ApplicationId,
    GroupId,
    ReviewItemId,
)
from housing_processor.domain.shared.value_objects import (
    ConfidenceScore,
    EmailAddress,
    PersonName,
    PhoneNumber,
)
from housing_processor.infrastructure.database.models.applicants import ApplicantModel
from housing_processor.infrastructure.database.models.applications import ApplicationModel
from housing_processor.infrastructure.database.models.audit import AuditEventModel
from housing_processor.infrastructure.database.models.groups import GroupMemberModel, GroupModel
from housing_processor.infrastructure.database.models.reviews import ReviewItemModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def application_to_domain(model: ApplicationModel) -> ApplicationRecord:
    return ApplicationRecord(
        id=ApplicationId(model.id),
        file_hash=model.file_hash,
        original_filename=model.original_filename,
        storage_key=model.storage_key,
        status=ApplicationStatus(model.status),
        received_at=model.received_at,
        source=model.source,
        version=model.version,
        duplicate_of_application_id=(
            ApplicationId(model.duplicate_of_application_id)
            if model.duplicate_of_application_id
            else None
        ),
        group_id=GroupId(model.group_id) if model.group_id else None,
        review_item_id=ReviewItemId(model.review_item_id) if model.review_item_id else None,
        parser_version=model.parser_version,
        matcher_version=model.matcher_version,
        failure_reason=model.failure_reason,
        warnings=json.loads(model.warnings_json or "[]"),
        idempotency_key=model.idempotency_key,
        created_by=model.created_by,
    )


def application_to_model(entity: ApplicationRecord, *, existing: ApplicationModel | None = None) -> ApplicationModel:
    now = _utcnow()
    model = existing or ApplicationModel(
        id=UUID(str(entity.id)),
        created_at=now,
    )
    model.file_hash = entity.file_hash
    model.original_filename = entity.original_filename
    model.storage_key = entity.storage_key
    model.status = entity.status.value
    model.received_at = entity.received_at
    model.source = entity.source
    model.version = entity.version
    model.duplicate_of_application_id = (
        UUID(str(entity.duplicate_of_application_id)) if entity.duplicate_of_application_id else None
    )
    model.group_id = UUID(str(entity.group_id)) if entity.group_id else None
    model.review_item_id = UUID(str(entity.review_item_id)) if entity.review_item_id else None
    model.parser_version = entity.parser_version
    model.matcher_version = entity.matcher_version
    model.failure_reason = entity.failure_reason
    model.warnings_json = json.dumps(entity.warnings)
    model.idempotency_key = entity.idempotency_key
    model.created_by = entity.created_by
    model.updated_at = now
    if existing is None:
        model.created_at = now
    return model


def applicant_to_domain(model: ApplicantModel) -> Applicant:
    email = None
    if model.email_normalized:
        email = EmailAddress(
            original=model.email_original or model.email_normalized,
            normalized=model.email_normalized,
        )
    phone = None
    if model.phone_e164:
        phone = PhoneNumber(
            original=model.phone_original or model.phone_e164,
            e164=model.phone_e164,
        )
    return Applicant(
        id=ApplicantId(model.id),
        name=PersonName(
            first=model.first_name,
            last=model.last_name,
            normalized=model.normalized_name,
        ),
        email=email,
        phone=phone,
        gpa=Decimal(model.gpa) if model.gpa is not None else None,
        created_at=model.created_at,
        version=model.version,
    )


def group_to_domain(model: GroupModel, members: list[GroupMemberModel]) -> HousingGroup:
    return HousingGroup(
        id=GroupId(model.id),
        group_number=model.group_number,
        status=GroupStatus(model.status),
        first_application_received_at=model.first_application_received_at,
        members=[
            GroupMember(
                applicant_id=ApplicantId(m.applicant_id),
                is_contact=m.is_contact,
                match_method=MatchMethod(m.match_method),
                match_confidence=ConfidenceScore(m.match_confidence),
                source_application_id=ApplicationId(m.source_application_id),
                joined_at=m.joined_at,
            )
            for m in members
        ],
        version=model.version,
    )


def review_to_domain(model: ReviewItemModel) -> ReviewItem:
    return ReviewItem(
        id=ReviewItemId(model.id),
        application_id=ApplicationId(model.application_id),
        status=ReviewStatus(model.status),
        reason_codes=tuple(json.loads(model.reason_codes_json or "[]")),
        created_at=model.created_at,
        version=model.version,
        suggested_group_id=GroupId(model.suggested_group_id) if model.suggested_group_id else None,
        resolved_at=model.resolved_at,
        resolved_by=model.resolved_by,
        resolution_notes=model.resolution_notes,
        evidence_summary=json.loads(model.evidence_summary_json or "[]"),
    )


def audit_to_model(event: AuditEvent) -> AuditEventModel:
    return AuditEventModel(
        id=uuid4(),
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        actor_id=event.actor_id,
        request_id=event.request_id,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        payload_json=json.dumps(event.payload),
    )
