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


class UpsertApplicantRequest(BaseModel):
    expected_version: int
    full_name: str
    email: str | None = None
    phone: str | None = None
    gpa: str | None = None
    applicant_id: UUID | None = None
    reason: str = "manual_correction"


class PropertyChoiceResponse(BaseModel):
    rank: int
    raw: str


class ApplicationDetailResponse(BaseModel):
    application_id: UUID
    status: ApplicationStatus
    original_filename: str
    received_at: datetime
    version: int
    group_id: UUID | None = None
    review_item_id: UUID | None = None
    review_required: bool = False
    warnings: list[str] = Field(default_factory=list)
    applicant_id: UUID | None = None
    applicant_name: str | None = None
    applicant_email: str | None = None
    applicant_phone: str | None = None
    applicant_gpa: str | None = None
    contact_person: str | None = None
    pending_roommates: list[str] = Field(default_factory=list)
    property_choices: list[PropertyChoiceResponse] = Field(default_factory=list)
