from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field

from housing_processor.presentation.api.contracts.applications import FieldCorrection


class AttachToGroupResolution(BaseModel):
    action: Literal["attach_to_group"]
    group_id: UUID


class CreateGroupResolution(BaseModel):
    action: Literal["create_group"]


class MarkDuplicateResolution(BaseModel):
    action: Literal["mark_duplicate"]
    duplicate_of_application_id: UUID


class RejectApplicationResolution(BaseModel):
    action: Literal["reject_application"]
    reason_code: str


ReviewResolution = Annotated[
    Union[
        AttachToGroupResolution,
        CreateGroupResolution,
        MarkDuplicateResolution,
        RejectApplicationResolution,
    ],
    Field(discriminator="action"),
]


class ResolveReviewRequest(BaseModel):
    resolution: ReviewResolution
    corrections: list[FieldCorrection] = Field(default_factory=list)
    expected_review_version: int
    notes: str | None = None
