"""Helpers for the extracted_v1: warning snapshot stored on applications."""

from __future__ import annotations

import json
from typing import Any

from housing_processor.application.contracts.extraction import ExtractedApplicationContract
from housing_processor.domain.applications.validation import ValidatedApplicationData
from housing_processor.infrastructure.docx import NA

EXTRACTED_V1_PREFIX = "extracted_v1:"


def _na(value: str | None) -> str:
    cleaned = (value or "").strip()
    return cleaned if cleaned else NA


def build_extracted_v1_snapshot(
    extracted: ExtractedApplicationContract,
    validated: ValidatedApplicationData,
) -> dict[str, Any]:
    """Build a JSON-serializable snapshot for UI/Excel (blanks as N/A)."""
    name = extracted.applicant.full_name.value if extracted.applicant.full_name else NA
    email = extracted.applicant.email.value if extracted.applicant.email else NA
    phone = extracted.applicant.phone.value if extracted.applicant.phone else NA
    gpa = extracted.gpa.value if extracted.gpa else NA

    contact = NA
    if validated.contact_person is not None:
        contact = f"{validated.contact_person.name.first} {validated.contact_person.name.last}".strip()
    elif extracted.contact_person is not None:
        contact = _na(extracted.contact_person.full_name.value)

    roommates: list[str] = []
    if validated.roommates:
        roommates = [
            f"{r.name.first} {r.name.last}".strip() for r in validated.roommates
        ]
    else:
        roommates = [
            _na(r.full_name.value) for r in extracted.roommates if r.full_name
        ]

    choices: dict[str, str] = {}
    for pref in validated.house_preferences:
        choices[str(pref.rank)] = _na(pref.raw_property)
    if not choices:
        for house in extracted.requested_houses:
            choices[str(house.rank)] = _na(house.raw_property)

    return {
        "name": _na(name),
        "email": _na(email),
        "phone": _na(phone),
        "gpa": _na(gpa),
        "contact_person": _na(contact),
        "roommates": roommates,
        "choices": {
            "1": choices.get("1", NA),
            "2": choices.get("2", NA),
            "3": choices.get("3", NA),
        },
    }


def encode_extracted_v1_warning(snapshot: dict[str, Any]) -> str:
    return EXTRACTED_V1_PREFIX + json.dumps(snapshot, separators=(",", ":"), sort_keys=True)


def parse_extracted_v1_snapshot(warnings: list[str] | tuple[str, ...]) -> dict[str, Any] | None:
    for warning in warnings:
        if not warning.startswith(EXTRACTED_V1_PREFIX):
            continue
        raw = warning[len(EXTRACTED_V1_PREFIX) :]
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return None


def replace_extracted_v1_warning(
    warnings: list[str],
    snapshot: dict[str, Any],
) -> list[str]:
    cleaned = [w for w in warnings if not w.startswith(EXTRACTED_V1_PREFIX)]
    cleaned.append(encode_extracted_v1_warning(snapshot))
    return cleaned


def property_prefs_from_snapshot(snapshot: dict[str, Any] | None) -> list[str]:
    if not snapshot:
        return []
    choices = snapshot.get("choices") or {}
    prefs: list[str] = []
    for rank in ("1", "2", "3"):
        value = _na(str(choices.get(rank, NA)))
        if value.upper() != NA:
            prefs.append(value)
    return prefs
