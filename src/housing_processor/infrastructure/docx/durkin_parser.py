"""Durkin Cottages Student Rental Application deterministic parser."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from housing_processor.application.contracts.extraction import (
    ExtractedApplicationContract,
    ExtractedValue,
    HousePreferenceContract,
    PersonReferenceContract,
    RawDocumentContent,
)

PARSER_VERSION = "durkin-label-parser-0.1.0"
NA = "N/A"
_SOURCE = "durkin_deterministic_parser"

# Labels mapped for ops (SSN intentionally omitted from persistence path).
_LABELS = (
    "1st Choice",
    "2nd Choice",
    "3rd Choice",
    "Contact Person of Group",
    "List Others in Group",
    "Name",
    "Middle",
    "Last",
    "Cell Phone Number",
    "Email",
    "Cumulative GPA",
    "Date of Birth",
    "Co-Signer (parent) First Name",
    "Co-Signer (parent) Email Address",
    "Phone Number",
    "What Year Are You In School?",
    "Year of Graduation",
    "Major",
)


def _empty_str() -> ExtractedValue[str]:
    return ExtractedValue[str](
        value=NA,
        raw_value=None,
        source=_SOURCE,
        confidence=0.0,
    )


def _str_value(raw: str | None, *, confidence: float = 0.9) -> ExtractedValue[str]:
    cleaned = (raw or "").strip()
    if not cleaned:
        return _empty_str()
    return ExtractedValue[str](
        value=cleaned,
        raw_value=cleaned,
        source=_SOURCE,
        confidence=confidence,
    )


def _is_blank(value: str | None) -> bool:
    return value is None or not str(value).strip() or str(value).strip().upper() == NA


def _filename_name_hint(filename: str | None) -> str | None:
    if not filename:
        return None
    stem = filename.rsplit("/", 1)[-1]
    stem = re.sub(r"\.docx$", "", stem, flags=re.IGNORECASE)
    # 00000001-Patrick-Sullivan-Student-App
    match = re.match(
        r"^\d+-(.+?)-Student-App$",
        stem,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    parts = [p for p in match.group(1).replace("_", "-").split("-") if p]
    if not parts:
        return None
    return " ".join(parts)


def _extract_labeled_fields(text: str) -> dict[str, str]:
    """Pull values after known labels from flat paragraph/tab form text.

    Durkin forms put several ``Label: value`` pairs on one line, separated by
    tabs or spaces (e.g. ``1st Choice: 14 Hope\\t2nd Choice: ...``). We locate
    every label occurrence (longest first so ``Cell Phone Number`` wins over
    ``Phone Number``), then take the slice until the next label.
    """
    flat = text.replace("\r\n", "\n")
    # Guard labels that contain shorter ones as suffixes (e.g. Last Name → Name).
    scan_labels = tuple(dict.fromkeys(_LABELS + ("Last Name", "First Name")))

    occurrences: list[tuple[int, int, str]] = []
    claimed: list[tuple[int, int]] = []
    for label in sorted(scan_labels, key=len, reverse=True):
        pattern = re.compile(
            rf"(?<![A-Za-z0-9]){re.escape(label)}\s*:",
            re.IGNORECASE,
        )
        for match in pattern.finditer(flat):
            start, end = match.start(), match.end()
            if any(not (end <= cs or start >= ce) for cs, ce in claimed):
                continue
            claimed.append((start, end))
            occurrences.append((start, end, label))

    occurrences.sort(key=lambda item: item[0])
    found: dict[str, str] = {}
    for index, (_start, end, label) in enumerate(occurrences):
        if label not in _LABELS:
            continue
        value_end = (
            occurrences[index + 1][0] if index + 1 < len(occurrences) else len(flat)
        )
        value = flat[end:value_end]
        # Values stay on the same visual line in this form.
        value = value.split("\n", 1)[0].strip()
        value = value.strip("\t ").strip()
        if label not in found:
            found[label] = value
    return found


class DurkinDeterministicParser:
    """Parse Durkin Student Rental Application label/tab forms."""

    def parse(self, document: RawDocumentContent) -> ExtractedApplicationContract:
        warnings = list(document.extraction_warnings)
        fields = _extract_labeled_fields(document.combined_text)

        first = fields.get("Name", "").strip()
        middle = fields.get("Middle", "").strip()
        last = fields.get("Last", "").strip()
        full_parts = [p for p in (first, middle, last) if p]
        full_name = " ".join(full_parts).strip()
        if _is_blank(full_name):
            hint = _filename_name_hint(document.source_filename)
            if hint:
                full_name = hint
                warnings.append("Applicant name taken from filename (form Name fields blank).")
            else:
                full_name = NA
                warnings.append("Applicant name missing; set to N/A.")

        email = fields.get("Email", "")
        # Applicant cell only — do not fall back to co-signer "Phone Number".
        phone = fields.get("Cell Phone Number", "")
        gpa_raw = fields.get("Cumulative GPA", "")
        contact_raw = fields.get("Contact Person of Group", "")
        others_raw = fields.get("List Others in Group", "")

        roommates: list[PersonReferenceContract] = []
        if not _is_blank(others_raw):
            for chunk in re.split(r",|;", others_raw):
                name = chunk.strip()
                if not name:
                    continue
                roommates.append(
                    PersonReferenceContract(
                        full_name=_str_value(name),
                        email=_empty_str(),
                        phone=_empty_str(),
                    )
                )

        houses: list[HousePreferenceContract] = []
        for rank, label in ((1, "1st Choice"), (2, "2nd Choice"), (3, "3rd Choice")):
            raw = fields.get(label, "").strip()
            houses.append(
                HousePreferenceContract(
                    raw_property=raw if raw else NA,
                    normalized_property_id=None,
                    rank=rank,
                    confidence=0.9 if raw else 0.0,
                )
            )

        gpa_value: ExtractedValue[str]
        if _is_blank(gpa_raw):
            gpa_value = _empty_str()
        else:
            try:
                Decimal(gpa_raw)
                gpa_value = _str_value(gpa_raw)
            except (InvalidOperation, ValueError):
                gpa_value = _str_value(gpa_raw, confidence=0.5)
                warnings.append(f"GPA value may be non-numeric: {gpa_raw!r}")

        contact = None
        if not _is_blank(contact_raw):
            contact = PersonReferenceContract(
                full_name=_str_value(contact_raw),
                email=_empty_str(),
                phone=_empty_str(),
            )

        for label in ("Name", "Email", "Cell Phone Number", "Cumulative GPA"):
            if label not in fields or _is_blank(fields.get(label)):
                warnings.append(f"Field '{label}' empty → N/A")

        expected_size = 1 + len(roommates) if roommates else None

        return ExtractedApplicationContract(
            schema_version="1.0",
            applicant=PersonReferenceContract(
                full_name=_str_value(full_name, confidence=0.85 if full_name != NA else 0.0),
                email=_str_value(email),
                phone=_str_value(phone),
            ),
            gpa=gpa_value,
            contact_person=contact,
            roommates=roommates,
            requested_houses=houses,
            expected_group_size=ExtractedValue[int](
                value=expected_size,
                raw_value=str(expected_size) if expected_size is not None else None,
                source=_SOURCE,
                confidence=0.7 if expected_size is not None else 0.0,
            ),
            warnings=warnings,
        )
