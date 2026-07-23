from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from housing_processor.application.extraction_snapshot import (
    build_extracted_v1_snapshot,
    parse_extracted_v1_snapshot,
    property_prefs_from_snapshot,
    replace_extracted_v1_warning,
)
from housing_processor.application.contracts.extraction import RawDocumentContent
from housing_processor.domain.groups.entities import GroupMember, HousingGroup
from housing_processor.domain.shared.enums import GroupStatus, MatchMethod
from housing_processor.domain.shared.identifiers import ApplicantId, ApplicationId, GroupId
from housing_processor.domain.shared.value_objects import ConfidenceScore
from housing_processor.infrastructure.database.repositories import SqlAlchemyGroupRepository
from housing_processor.infrastructure.docx import (
    DurkinApplicationValidator,
    DurkinDeterministicParser,
    PythonDocxDocumentReader,
)
from pathlib import Path


PARSER = DurkinDeterministicParser()
VALIDATOR = DurkinApplicationValidator()
READER = PythonDocxDocumentReader()
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "00000001-Patrick-Sullivan-Student-App.docx"


def test_cell_phone_ignores_cosigner_phone_number() -> None:
    document = RawDocumentContent(
        paragraphs=[],
        tables=[],
        combined_text=(
            "Name: Jane\tMiddle: \tLast: Doe\tCell Phone Number: \n"
            "Email: jane@example.com\tDate of Birth: \n"
            "Co-Signer (parent) Email Address: parent@example.com\tPhone Number: 4015551212\n"
            "Cumulative GPA: 3.2\n"
        ),
        extraction_warnings=[],
        source_filename=None,
    )
    result = PARSER.parse(document)
    assert result.applicant.phone.value == "N/A"
    assert result.applicant.email.value == "jane@example.com"
    assert result.gpa.value == "3.2"


def test_extracted_v1_snapshot_from_sparse_fixture() -> None:
    document = READER.read(FIXTURE)
    extracted = PARSER.parse(document)
    validated = VALIDATOR.validate(extracted)
    snapshot = build_extracted_v1_snapshot(extracted, validated)

    assert snapshot["name"] == "Patrick Sullivan"
    assert snapshot["email"] == "N/A"
    assert snapshot["phone"] == "N/A"
    assert snapshot["gpa"] == "3.5"
    assert snapshot["contact_person"] == "Patrick Sullivan"
    assert snapshot["roommates"] == ["Drew Conroy", "David McGinn", "Carter Paine"]
    assert snapshot["choices"] == {"1": "14 Hope", "2": "14 Hope", "3": "14 Hope"}

    warnings = replace_extracted_v1_warning([], snapshot)
    parsed = parse_extracted_v1_snapshot(warnings)
    assert parsed is not None
    assert parsed["gpa"] == "3.5"
    assert property_prefs_from_snapshot(parsed) == ["14 Hope", "14 Hope", "14 Hope"]


def test_group_repository_add_flushes_before_members() -> None:
    session = MagicMock()
    flush_order: list[str] = []

    def track_add(obj):  # type: ignore[no-untyped-def]
        name = type(obj).__name__
        flush_order.append(f"add:{name}")

    def track_flush():
        flush_order.append("flush")

    session.add.side_effect = track_add
    session.flush.side_effect = track_flush

    repo = SqlAlchemyGroupRepository(session)
    now = datetime.now(timezone.utc)
    group = HousingGroup(
        id=GroupId(uuid4()),
        group_number=1,
        status=GroupStatus.INCOMPLETE,
        first_application_received_at=now,
        members=[
            GroupMember(
                applicant_id=ApplicantId(uuid4()),
                is_contact=True,
                match_method=MatchMethod.MANUAL,
                match_confidence=ConfidenceScore(1.0),
                source_application_id=ApplicationId(uuid4()),
                joined_at=now,
            )
        ],
        version=1,
    )
    repo.add(group)

    assert flush_order[0].startswith("add:GroupModel")
    assert "flush" in flush_order
    assert flush_order.index("flush") < flush_order.index("add:GroupMemberModel")
