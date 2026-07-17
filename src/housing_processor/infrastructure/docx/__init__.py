from pathlib import Path

from docx import Document

from housing_processor.application.contracts.extraction import (
    DocumentParagraph,
    DocumentTable,
    ExtractedApplicationContract,
    ExtractedValue,
    PersonReferenceContract,
    RawDocumentContent,
    TextRun,
)
from housing_processor.domain.applications.validation import (
    ValidatedApplicationData,
    ValidationIssue,
)
from housing_processor.domain.applicants.entities import ApplicantCandidate
from housing_processor.domain.shared.value_objects import PersonName


PARSER_VERSION = "deterministic-stub-0.1.0"


class PythonDocxDocumentReader:
    def read(self, path: Path) -> RawDocumentContent:
        document = Document(str(path))
        paragraphs: list[DocumentParagraph] = []
        for index, paragraph in enumerate(document.paragraphs):
            runs = [
                TextRun(text=run.text, bold=bool(run.bold), italic=bool(run.italic))
                for run in paragraph.runs
            ]
            paragraphs.append(
                DocumentParagraph(index=index, text=paragraph.text, runs=runs)
            )

        tables: list[DocumentTable] = []
        for index, table in enumerate(document.tables):
            rows = [[cell.text for cell in row.cells] for row in table.rows]
            tables.append(DocumentTable(index=index, rows=rows))

        combined = "\n".join(p.text for p in paragraphs if p.text.strip())
        return RawDocumentContent(
            paragraphs=paragraphs,
            tables=tables,
            combined_text=combined,
            extraction_warnings=[],
        )


class StubDeterministicParser:
    """Phase 1 stub: returns an empty extracted contract shell with provenance."""

    def parse(self, document: RawDocumentContent) -> ExtractedApplicationContract:
        warnings = list(document.extraction_warnings)
        warnings.append("Deterministic parser stub — field mapping not yet implemented.")
        empty_name = ExtractedValue[str](
            value=None,
            raw_value=None,
            source="deterministic_parser",
            confidence=0.0,
            warnings=["Applicant name not extracted (stub)."],
        )
        return ExtractedApplicationContract(
            schema_version="1.0",
            applicant=PersonReferenceContract(full_name=empty_name),
            warnings=warnings,
        )


class PassThroughStructuredExtractor:
    """Phase 1: returns the deterministic result unchanged (LLM disabled)."""

    def extract(
        self,
        document: RawDocumentContent,
        deterministic_result: ExtractedApplicationContract,
    ) -> ExtractedApplicationContract:
        _ = document
        return deterministic_result


class StubApplicationValidator:
    """Accepts incomplete extractions with validation warnings for Phase 1 scaffolding."""

    def validate(self, extracted: ExtractedApplicationContract) -> ValidatedApplicationData:
        issues: list[ValidationIssue] = []
        name_value = extracted.applicant.full_name.value or "Unknown Applicant"
        parts = name_value.strip().split(None, 1)
        first = parts[0] if parts else "Unknown"
        last = parts[1] if len(parts) > 1 else "Applicant"
        normalized = f"{first} {last}".casefold()

        if extracted.applicant.full_name.value is None:
            issues.append(
                ValidationIssue(
                    code="applicant.name_missing",
                    field_path="applicant.full_name",
                    severity="warning",
                    message="Applicant name was not extracted.",
                )
            )

        candidate = ApplicantCandidate(
            name=PersonName(first=first, last=last, normalized=normalized),
            email=None,
            phone=None,
            gpa=None,
        )
        return ValidatedApplicationData(
            applicant=candidate,
            roommates=tuple(),
            contact_person=None,
            house_preferences=tuple(),
            expected_group_size=None,
            application_date=None,
            issues=tuple(issues),
        )
