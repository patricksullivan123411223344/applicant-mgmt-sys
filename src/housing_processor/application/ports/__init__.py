"""Application-layer protocols for adapters and repositories."""

from housing_processor.application.ports.extractors import (
    ApplicationValidator,
    DeterministicParser,
    DocumentReader,
    StructuredApplicationExtractor,
)
from housing_processor.application.ports.matching import ApplicantIdentityResolver, GroupMatcher
from housing_processor.application.ports.repositories import (
    ApplicantRepository,
    ApplicationRepository,
    AuditRepository,
    GroupRepository,
    ReviewRepository,
    UnitOfWork,
    UnitOfWorkFactory,
)
from housing_processor.application.ports.support import Clock, IdGenerator
from housing_processor.application.ports.storage import ExcelRenderer, FileStorage

__all__ = [
    "ApplicantIdentityResolver",
    "ApplicantRepository",
    "ApplicationRepository",
    "ApplicationValidator",
    "AuditRepository",
    "Clock",
    "DeterministicParser",
    "DocumentReader",
    "ExcelRenderer",
    "FileStorage",
    "GroupMatcher",
    "GroupRepository",
    "IdGenerator",
    "ReviewRepository",
    "StructuredApplicationExtractor",
    "UnitOfWork",
    "UnitOfWorkFactory",
]
