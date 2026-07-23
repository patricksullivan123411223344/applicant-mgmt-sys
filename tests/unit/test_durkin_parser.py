from pathlib import Path

import pytest

from housing_processor.infrastructure.docx import (
    DurkinDeterministicParser,
    PythonDocxDocumentReader,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
PARSER = DurkinDeterministicParser()
READER = PythonDocxDocumentReader()


@pytest.mark.parametrize(
    ("filename", "expected_name"),
    [
        ("00000001-Patrick-Sullivan-Student-App.docx", "Patrick Sullivan"),
        ("00000002-John-Doe-Student-App.docx", "John Doe"),
        ("00000003-Jane-Doe-Student-App.docx", "Jane Doe"),
        ("00000004-Tim-Doe-Student-App.docx", "Tim Doe"),
    ],
)
def test_durkin_sparse_fixtures(filename: str, expected_name: str) -> None:
    path = FIXTURES / filename
    assert path.exists(), f"Missing fixture {path}"
    document = READER.read(path)
    result = PARSER.parse(document)

    assert result.applicant.full_name.value == expected_name
    assert result.applicant.email.value == "N/A"
    assert result.applicant.phone.value == "N/A"
    assert result.contact_person is not None
    assert result.contact_person.full_name.value == "Patrick Sullivan"
    assert [r.full_name.value for r in result.roommates] == [
        "Drew Conroy",
        "David McGinn",
        "Carter Paine",
    ]
    assert [(h.rank, h.raw_property) for h in result.requested_houses] == [
        (1, "14 Hope"),
        (2, "14 Hope"),
        (3, "14 Hope"),
    ]
    assert result.gpa.value == "3.5"


def test_blank_labels_become_na() -> None:
    from housing_processor.application.contracts.extraction import RawDocumentContent

    document = RawDocumentContent(
        paragraphs=[],
        tables=[],
        combined_text="Name: \tEmail: \tCell Phone Number: \nCumulative GPA: ",
        extraction_warnings=[],
        source_filename=None,
    )
    result = PARSER.parse(document)
    assert result.applicant.full_name.value == "N/A"
    assert result.applicant.email.value == "N/A"
    assert result.applicant.phone.value == "N/A"
    assert result.gpa.value == "N/A"
