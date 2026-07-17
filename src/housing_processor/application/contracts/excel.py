from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class WorkbookApplicantRow(BaseModel):
    group_number: int
    applicant_name: str
    is_contact: bool
    phone: str | None = None
    email: str | None = None
    gpa: Decimal | None = None
    requested_properties: list[str] = Field(default_factory=list)
    expected_group_size: int | None = None
    application_received_date: date | None = None
    group_status: str
    review_notes: str | None = None


class HousingWorkbookProjection(BaseModel):
    generated_at: datetime
    export_id: UUID | None = None
    rows: list[WorkbookApplicantRow] = Field(default_factory=list)
