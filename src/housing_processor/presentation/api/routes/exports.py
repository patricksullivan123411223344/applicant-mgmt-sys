from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse

from housing_processor.application.commands.export import CreateExcelExportCommand
from housing_processor.application.dto.actor import ActorContext
from housing_processor.bootstrap import AppContainer
from housing_processor.infrastructure.database.models.exports import ExcelExportModel
from housing_processor.presentation.api.contracts.common import PageMeta, PaginatedResponse
from housing_processor.presentation.api.contracts.exports import (
    CreateExcelExportRequest,
    ExcelExportAcceptedResponse,
)
from housing_processor.presentation.api.dependencies import get_actor_context, get_app_container
from housing_processor.domain.shared.errors import ResourceNotFoundError

router = APIRouter(
    prefix="/exports",
    tags=["exports"],
    dependencies=[Depends(get_actor_context)],
)


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
    _ = body
    export_id, export_status = container.excel_export_handler.handle(
        CreateExcelExportCommand(actor=actor)
    )
    return ExcelExportAcceptedResponse(export_id=UUID(export_id), status=export_status)


@router.get("")
def list_exports(
    limit: int = 50,
    offset: int = 0,
    container: AppContainer = Depends(get_app_container),
) -> PaginatedResponse[dict]:
    with container.uow_factory() as uow:
        assert uow.session is not None
        rows = list(
            uow.session.query(ExcelExportModel)
            .order_by(ExcelExportModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        total = uow.session.query(ExcelExportModel).count()
        items = [
            {
                "export_id": str(row.id),
                "status": row.status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            }
            for row in rows
        ]
        return PaginatedResponse(items=items, page=PageMeta(limit=limit, offset=offset, total=total))


@router.get("/{export_id}")
def get_export(export_id: UUID, container: AppContainer = Depends(get_app_container)) -> dict:
    with container.uow_factory() as uow:
        assert uow.session is not None
        row = uow.session.get(ExcelExportModel, export_id)
        if row is None:
            raise ResourceNotFoundError(f"Export {export_id} was not found.")
        return {
            "export_id": str(row.id),
            "status": row.status,
            "storage_key": row.storage_key,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        }


@router.get("/{export_id}/download")
def download_export(export_id: UUID, container: AppContainer = Depends(get_app_container)):
    with container.uow_factory() as uow:
        assert uow.session is not None
        row = uow.session.get(ExcelExportModel, export_id)
        if row is None or not row.storage_key:
            raise ResourceNotFoundError(f"Export {export_id} was not found.")
        path = container.storage.resolve_path(row.storage_key)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"housing-export-{export_id}.xlsx",
    )
