from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from housing_processor.domain.shared.enums import GroupStatus


class CreateExcelExportRequest(BaseModel):
    include_group_statuses: list[GroupStatus] = Field(
        default_factory=lambda: [
            GroupStatus.INCOMPLETE,
            GroupStatus.ACTIVE,
            GroupStatus.COMPLETE,
            GroupStatus.REVIEW_REQUIRED,
        ]
    )
    as_of: datetime | None = None


class ExcelExportAcceptedResponse(BaseModel):
    export_id: UUID
    status: str = "accepted"
