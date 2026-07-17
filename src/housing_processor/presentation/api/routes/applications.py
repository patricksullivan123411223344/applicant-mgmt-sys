from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status

from housing_processor.application.commands.ingest import IngestApplicationCommand
from housing_processor.application.dto.actor import ActorContext
from housing_processor.bootstrap import AppContainer
from housing_processor.domain.shared.enums import ApplicationStatus
from housing_processor.presentation.api.contracts.applications import (
    ApplicationAcceptedResponse,
    ApplicationSummaryResponse,
    CorrectExtractedDataRequest,
    ReprocessApplicationRequest,
)
from housing_processor.presentation.api.contracts.common import PageMeta, PaginatedResponse
from housing_processor.presentation.api.dependencies import get_actor_context, get_app_container

router = APIRouter(prefix="/applications", tags=["applications"])


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


@router.get("/{application_id}", response_model=ApplicationSummaryResponse)
def get_application(
    application_id: UUID,
    container: AppContainer = Depends(get_app_container),
) -> ApplicationSummaryResponse:
    from housing_processor.domain.shared.identifiers import ApplicationId

    with container.uow_factory() as uow:
        record = uow.applications.get(ApplicationId(application_id))
        return ApplicationSummaryResponse(
            application_id=UUID(str(record.id)),
            status=record.status,
            original_filename=record.original_filename,
            received_at=record.received_at,
            group_id=UUID(str(record.group_id)) if record.group_id else None,
            review_required=record.status == ApplicationStatus.REVIEW_REQUIRED,
        )


@router.post("/{application_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
def reprocess_application(
    application_id: UUID,
    body: ReprocessApplicationRequest,
    actor: ActorContext = Depends(get_actor_context),
    container: AppContainer = Depends(get_app_container),
) -> dict[str, object]:
    from housing_processor.application.commands.process import ProcessApplicationCommand
    from housing_processor.domain.shared.identifiers import ApplicationId

    _ = body
    result = container.process_handler.handle(
        ProcessApplicationCommand(
            application_id=ApplicationId(application_id),
            actor=actor,
            force_reprocess=True,
        )
    )
    return {
        "application_id": str(result.application_id),
        "status": result.status.value,
        "warnings": list(result.warnings),
    }


@router.patch("/{application_id}/extracted-data", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def correct_extracted_data(
    application_id: UUID,
    body: CorrectExtractedDataRequest,
) -> dict[str, str]:
    _ = application_id, body
    return {"detail": "Extracted-data correction is not implemented in Phase 1 scaffold."}
