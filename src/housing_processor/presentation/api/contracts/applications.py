from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from housing_processor.domain.shared.enums import ApplicationStatus


class ApplicationAcceptedResponse(BaseModel):
    application_id: UUID
    status: ApplicationStatus
    duplicate_of_application_id: UUID | None = None
    received_at: datetime


class ApplicationSummaryResponse(BaseModel):
    application_id: UUID
    status: ApplicationStatus
    original_filename: str
    received_at: datetime
    group_id: UUID | None = None
    review_required: bool = False


class ReprocessApplicationRequest(BaseModel):
    expected_version: int
    extraction_mode: str = "current"
    preserve_confirmed_decisions: bool = True
    reason: str


class FieldCorrection(BaseModel):
    field_path: str
    new_value: str | None = None
    reason: str


class CorrectExtractedDataRequest(BaseModel):
    expected_version: int
    corrections: list[FieldCorrection] = Field(default_factory=list)
    reason: str
