from pathlib import Path
from typing import Protocol

from housing_processor.application.contracts.extraction import (
    ExtractedApplicationContract,
    RawDocumentContent,
)
from housing_processor.domain.applications.validation import ValidatedApplicationData


class DocumentReader(Protocol):
    def read(self, path: Path) -> RawDocumentContent: ...


class DeterministicParser(Protocol):
    def parse(self, document: RawDocumentContent) -> ExtractedApplicationContract: ...


class StructuredApplicationExtractor(Protocol):
    def extract(
        self,
        document: RawDocumentContent,
        deterministic_result: ExtractedApplicationContract,
    ) -> ExtractedApplicationContract: ...


class ApplicationValidator(Protocol):
    def validate(self, extracted: ExtractedApplicationContract) -> ValidatedApplicationData: ...
