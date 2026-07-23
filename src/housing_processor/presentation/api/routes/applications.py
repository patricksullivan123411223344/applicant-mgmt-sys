from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status

from housing_processor.application.commands.ingest import IngestApplicationCommand
from housing_processor.application.dto.actor import ActorContext
from housing_processor.bootstrap import AppContainer
from housing_processor.domain.shared.enums import ApplicationStatus
from housing_processor.domain.shared.identifiers import ApplicantId, ApplicationId
from housing_processor.application.extraction_snapshot import parse_extracted_v1_snapshot
from housing_processor.infrastructure.docx import NA
from housing_processor.presentation.api.contracts.applications import (
    ApplicationAcceptedResponse,
    ApplicationDetailResponse,
    ApplicationSummaryResponse,
    PropertyChoiceResponse,
    ReprocessApplicationRequest,
    UpsertApplicantRequest,
)
from housing_processor.presentation.api.contracts.common import PageMeta, PaginatedResponse
from housing_processor.presentation.api.dependencies import get_actor_context, get_app_container

router = APIRouter(
    prefix="/applications",
    tags=["applications"],
    dependencies=[Depends(get_actor_context)],
)


def _find_linked_applicant(uow, application):  # type: ignore[no-untyped-def]
    """Best-effort: applicant id recorded in warnings after process/upsert."""
    for warning in application.warnings:
        if warning.startswith("applicant.upserted:"):
            try:
                return uow.applicants.get(ApplicantId(UUID(warning.split(":", 1)[1])))
            except Exception:
                continue
    # Fallback: search by filename-ish name not available; return None
    return None


@router.post(
    "",
    response_model=ApplicationAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_application(
    request: Request,
    file: UploadFile = File(...),
    received_at: datetime | None = Form(default=None),
    source: str = Form(default="manual_upload"),
    actor: ActorContext = Depends(get_actor_context),
    container: AppContainer = Depends(get_app_container),
) -> ApplicationAcceptedResponse:
    _ = request
    content = await file.read()
    if len(content) > container.settings.max_upload_bytes:
        from housing_processor.domain.shared.errors import DomainError

        raise DomainError(
            "Uploaded file exceeds the configured size limit.",
            context={"max_upload_bytes": container.settings.max_upload_bytes},
        )

    filename = file.filename or "application.docx"
    content_type = file.content_type or ""
    allowed = container.settings.allowed_document_types
    if content_type and content_type not in allowed and not filename.lower().endswith(".docx"):
        from housing_processor.domain.shared.errors import DomainError

        err = DomainError(
            "Unsupported document type. Only .docx applications are accepted.",
            context={"content_type": content_type},
            code="application.unsupported_document",
        )
        raise err

    result = container.ingest_handler.handle(
        IngestApplicationCommand(
            content=content,
            filename=filename,
            actor=actor,
            received_at=received_at,
            source=source,
        )
    )
    return ApplicationAcceptedResponse(
        application_id=UUID(str(result.application_id)),
        status=result.status,
        duplicate_of_application_id=(
            UUID(str(result.duplicate_of_application_id))
            if result.duplicate_of_application_id
            else None
        ),
        received_at=result.received_at,  # type: ignore[arg-type]
    )


@router.get("", response_model=PaginatedResponse[ApplicationSummaryResponse])
def list_applications(
    status_filter: ApplicationStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    container: AppContainer = Depends(get_app_container),
) -> PaginatedResponse[ApplicationSummaryResponse]:
    with container.uow_factory() as uow:
        records, total = uow.applications.list(
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        items = [
            ApplicationSummaryResponse(
                application_id=UUID(str(record.id)),
                status=record.status,
                original_filename=record.original_filename,
                received_at=record.received_at,
                group_id=UUID(str(record.group_id)) if record.group_id else None,
                review_required=record.status == ApplicationStatus.REVIEW_REQUIRED,
            )
            for record in records
        ]
        return PaginatedResponse(
            items=items,
            page=PageMeta(limit=limit, offset=offset, total=total),
        )


def _display_or_na(*candidates: str | None) -> str | None:
    """Prefer first non-empty candidate; once processed prefer explicit N/A over null."""
    for value in candidates:
        if value is None:
            continue
        cleaned = str(value).strip()
        if cleaned:
            return cleaned
    return None


@router.get("/{application_id}", response_model=ApplicationDetailResponse)
def get_application(
    application_id: UUID,
    container: AppContainer = Depends(get_app_container),
) -> ApplicationDetailResponse:
    with container.uow_factory() as uow:
        record = uow.applications.get(ApplicationId(application_id))
        applicant = None
        for warning in record.warnings:
            if warning.startswith("applicant.upserted:"):
                try:
                    applicant = uow.applicants.get(ApplicantId(UUID(warning.split(":", 1)[1])))
                    break
                except Exception:
                    continue

        snapshot = parse_extracted_v1_snapshot(record.warnings)
        processed = snapshot is not None

        applicant_name = None
        if applicant:
            applicant_name = f"{applicant.name.first} {applicant.name.last}".strip()
        if not applicant_name and snapshot:
            applicant_name = snapshot.get("name")

        email_from_applicant = (
            applicant.email.original if applicant and applicant.email else None
        )
        phone_from_applicant = (
            applicant.phone.original if applicant and applicant.phone else None
        )
        gpa_from_applicant = (
            str(applicant.gpa) if applicant and applicant.gpa is not None else None
        )

        email = _display_or_na(
            email_from_applicant,
            snapshot.get("email") if snapshot else None,
            NA if processed else None,
        )
        phone = _display_or_na(
            phone_from_applicant,
            snapshot.get("phone") if snapshot else None,
            NA if processed else None,
        )
        gpa = _display_or_na(
            gpa_from_applicant,
            snapshot.get("gpa") if snapshot else None,
            NA if processed else None,
        )

        contact_person = snapshot.get("contact_person") if snapshot else None
        roommates = list(snapshot.get("roommates") or []) if snapshot else []
        if not roommates:
            for warning in record.warnings:
                if warning.startswith("pending_roommates:"):
                    roommates = [
                        part.strip()
                        for part in warning.split(":", 1)[1].split("|")
                        if part.strip()
                    ]
                    break

        choices: list[PropertyChoiceResponse] = []
        if snapshot and isinstance(snapshot.get("choices"), dict):
            for rank in (1, 2, 3):
                raw = snapshot["choices"].get(str(rank), NA)
                choices.append(PropertyChoiceResponse(rank=rank, raw=str(raw or NA)))

        return ApplicationDetailResponse(
            application_id=UUID(str(record.id)),
            status=record.status,
            original_filename=record.original_filename,
            received_at=record.received_at,
            version=record.version,
            group_id=UUID(str(record.group_id)) if record.group_id else None,
            review_item_id=UUID(str(record.review_item_id)) if record.review_item_id else None,
            review_required=record.status == ApplicationStatus.REVIEW_REQUIRED,
            warnings=list(record.warnings),
            applicant_id=UUID(str(applicant.id)) if applicant else None,
            applicant_name=applicant_name,
            applicant_email=email,
            applicant_phone=phone,
            applicant_gpa=gpa,
            contact_person=contact_person,
            pending_roommates=roommates,
            property_choices=choices,
        )


@router.post("/{application_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
def reprocess_application(
    application_id: UUID,
    body: ReprocessApplicationRequest,
    actor: ActorContext = Depends(get_actor_context),
    container: AppContainer = Depends(get_app_container),
) -> dict[str, object]:
    from housing_processor.application.commands.process import ProcessApplicationCommand

    _ = body
    result = container.process_handler.handle(
        ProcessApplicationCommand(
            application_id=ApplicationId(application_id),
            actor=actor,
            force_reprocess=True,
        )
    )
    # Tag application with applicant id for detail lookup
    if result.applicant_id is not None:
        with container.uow_factory() as uow:
            application = uow.applications.get(ApplicationId(application_id))
            tag = f"applicant.upserted:{result.applicant_id}"
            if tag not in application.warnings:
                application.warnings = list(application.warnings) + [tag]
                uow.applications.save(application)
                uow.commit()

    return {
        "application_id": str(result.application_id),
        "status": result.status.value,
        "applicant_id": str(result.applicant_id) if result.applicant_id else None,
        "review_item_id": str(result.review_item_id) if result.review_item_id else None,
        "warnings": list(result.warnings),
    }


@router.put("/{application_id}/applicant")
def upsert_applicant(
    application_id: UUID,
    body: UpsertApplicantRequest,
    container: AppContainer = Depends(get_app_container),
) -> dict[str, object]:
    applicant = container.upsert_applicant_handler.handle(
        application_id=ApplicationId(application_id),
        expected_version=body.expected_version,
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        gpa=body.gpa,
        applicant_id=ApplicantId(body.applicant_id) if body.applicant_id else None,
    )
    return {
        "applicant_id": str(applicant.id),
        "full_name": f"{applicant.name.first} {applicant.name.last}".strip(),
        "email": applicant.email.original if applicant.email else None,
        "phone": applicant.phone.original if applicant.phone else None,
        "gpa": str(applicant.gpa) if applicant.gpa is not None else None,
    }
