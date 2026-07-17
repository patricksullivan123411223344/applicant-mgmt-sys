from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status

from housing_processor.application.dto.actor import ActorContext
from housing_processor.bootstrap import AppContainer
from housing_processor.presentation.api.contracts.common import PageMeta, PaginatedResponse
from housing_processor.presentation.api.contracts.exports import (
    CreateExcelExportRequest,
    ExcelExportAcceptedResponse,
)
from housing_processor.presentation.api.dependencies import get_actor_context, get_app_container

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post(
    "/excel",
    response_model=ExcelExportAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_excel_export(
    body: CreateExcelExportRequest,
    actor: ActorContext = Depends(get_actor_context),
    container: AppContainer = Depends(get_app_container),
) -> ExcelExportAcceptedResponse:
    _ = body, actor, container
    # Full export job wiring lands in a later Phase 1 slice.
    return ExcelExportAcceptedResponse(export_id=uuid4(), status="accepted")


@router.get("")
def list_exports(
    limit: int = 50,
    offset: int = 0,
    container: AppContainer = Depends(get_app_container),
) -> PaginatedResponse[dict]:
    _ = container
    return PaginatedResponse(items=[], page=PageMeta(limit=limit, offset=offset, total=0))


@router.get("/{export_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def get_export(export_id: UUID) -> dict[str, str]:
    return {"detail": f"Export {export_id} detail is not implemented in Phase 1 scaffold."}


@router.get("/{export_id}/download", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def download_export(export_id: UUID) -> dict[str, str]:
    return {"detail": f"Export download for {export_id} is not implemented in Phase 1 scaffold."}
