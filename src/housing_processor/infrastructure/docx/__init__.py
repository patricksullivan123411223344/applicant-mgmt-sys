from pathlib import Path
from decimal import Decimal, InvalidOperation

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
    PersonReference,
    ValidatedApplicationData,
    ValidationIssue,
)
from housing_processor.domain.applicants.entities import ApplicantCandidate
from housing_processor.domain.properties.entities import HousePreference
from housing_processor.domain.shared.value_objects import EmailAddress, PersonName, PhoneNumber
from housing_processor.infrastructure.docx.durkin_parser import (
    PARSER_VERSION,
    DurkinDeterministicParser,
    NA,
)

# Back-compat alias used by older imports/tests.
StubDeterministicParser = DurkinDeterministicParser


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
            source_filename=path.name,
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


def _split_name(full_name: str) -> PersonName:
    cleaned = (full_name or "").strip()
    if not cleaned or cleaned.upper() == NA:
        return PersonName(first="Unknown", last="Applicant", normalized="unknown applicant")
    parts = cleaned.split()
    first = parts[0]
    last = " ".join(parts[1:]) if len(parts) > 1 else "Applicant"
    normalized = f"{first} {last}".casefold()
    return PersonName(first=first, last=last, normalized=normalized)


def _email_or_none(raw: str | None) -> EmailAddress | None:
    if raw is None or not raw.strip() or raw.strip().upper() == NA:
        return None
    original = raw.strip()
    return EmailAddress(original=original, normalized=original.casefold())


def _phone_or_none(raw: str | None) -> PhoneNumber | None:
    if raw is None or not raw.strip() or raw.strip().upper() == NA:
        return None
    original = raw.strip()
    digits = "".join(ch for ch in original if ch.isdigit() or ch == "+")
    e164 = digits if digits.startswith("+") else f"+1{digits}" if len(digits) == 10 else digits
    if not e164:
        return None
    return PhoneNumber(original=original, e164=e164)


def _person_ref(contract: PersonReferenceContract | None) -> PersonReference | None:
    if contract is None:
        return None
    name_val = contract.full_name.value or NA
    return PersonReference(
        name=_split_name(name_val),
        email_raw=(contract.email.value if contract.email else None),
        phone_raw=(contract.phone.value if contract.phone else None),
    )


class DurkinApplicationValidator:
    """Normalize Durkin extractions; blanks stay N/A / None without failing the pipeline."""

    def validate(self, extracted: ExtractedApplicationContract) -> ValidatedApplicationData:
        issues: list[ValidationIssue] = []
        name_value = extracted.applicant.full_name.value or NA
        if name_value.upper() == NA:
            issues.append(
                ValidationIssue(
                    code="applicant.name_missing",
                    field_path="applicant.full_name",
                    severity="warning",
                    message="Applicant name was N/A after extraction.",
                )
            )

        gpa: Decimal | None = None
        if extracted.gpa and extracted.gpa.value and extracted.gpa.value.upper() != NA:
            try:
                gpa = Decimal(extracted.gpa.value)
            except (InvalidOperation, ValueError):
                issues.append(
                    ValidationIssue(
                        code="applicant.gpa_invalid",
                        field_path="gpa",
                        severity="warning",
                        message=f"Could not parse GPA {extracted.gpa.value!r}.",
                    )
                )

        email_raw = extracted.applicant.email.value if extracted.applicant.email else None
        phone_raw = extracted.applicant.phone.value if extracted.applicant.phone else None

        candidate = ApplicantCandidate(
            name=_split_name(name_value),
            email=_email_or_none(email_raw),
            phone=_phone_or_none(phone_raw),
            gpa=gpa,
        )

        roommates = tuple(
            ref
            for ref in (_person_ref(r) for r in extracted.roommates)
            if ref is not None
        )
        contact = _person_ref(extracted.contact_person)
        prefs = tuple(
            HousePreference(
                raw_property=h.raw_property,
                property_id=None,
                rank=h.rank,
                confidence=h.confidence,
            )
            for h in extracted.requested_houses
        )

        expected_size = None
        if extracted.expected_group_size and extracted.expected_group_size.value is not None:
            expected_size = int(extracted.expected_group_size.value)

        return ValidatedApplicationData(
            applicant=candidate,
            roommates=roommates,
            contact_person=contact,
            house_preferences=prefs,
            expected_group_size=expected_size,
            application_date=None,
            issues=tuple(issues),
        )


# Prefer Durkin validator as the Phase 1 default.
StubApplicationValidator = DurkinApplicationValidator

__all__ = [
    "PARSER_VERSION",
    "DurkinDeterministicParser",
    "DurkinApplicationValidator",
    "StubDeterministicParser",
    "StubApplicationValidator",
    "PythonDocxDocumentReader",
    "PassThroughStructuredExtractor",
]
