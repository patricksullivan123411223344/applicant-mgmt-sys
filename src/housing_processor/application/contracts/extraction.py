from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class TextRun(BaseModel):
    text: str
    bold: bool = False
    italic: bool = False


class DocumentParagraph(BaseModel):
    index: int
    text: str
    runs: list[TextRun]


class DocumentTable(BaseModel):
    index: int
    rows: list[list[str]]


class RawDocumentContent(BaseModel):
    paragraphs: list[DocumentParagraph]
    tables: list[DocumentTable]
    combined_text: str
    extraction_warnings: list[str] = Field(default_factory=list)


class ExtractedValue[T](BaseModel):
    value: T | None
    raw_value: str | None
    source: str
    confidence: float
    warnings: list[str] = Field(default_factory=list)


class PersonReferenceContract(BaseModel):
    full_name: ExtractedValue[str]
    email: ExtractedValue[str] | None = None
    phone: ExtractedValue[str] | None = None


class HousePreferenceContract(BaseModel):
    raw_property: str
    normalized_property_id: UUID | None
    rank: int | None
    confidence: float


class ExtractedApplicationContract(BaseModel):
    schema_version: str
    applicant: PersonReferenceContract
    gpa: ExtractedValue[str] | None = None
    contact_person: PersonReferenceContract | None = None
    roommates: list[PersonReferenceContract] = Field(default_factory=list)
    requested_houses: list[HousePreferenceContract] = Field(default_factory=list)
    expected_group_size: ExtractedValue[int] | None = None
    application_date: ExtractedValue[date] | None = None
    warnings: list[str] = Field(default_factory=list)
