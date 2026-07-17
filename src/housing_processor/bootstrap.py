"""Composition root: wire settings to concrete adapters (no business rules)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from housing_processor.application.handlers.ingest import IngestApplicationHandler
from housing_processor.application.handlers.process import ProcessApplicationHandler
from housing_processor.config import Settings, get_settings
from housing_processor.infrastructure.database.session import (
    create_engine_from_url,
    create_session_factory,
)
from housing_processor.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWorkFactory
from housing_processor.infrastructure.docx import (
    PassThroughStructuredExtractor,
    PythonDocxDocumentReader,
    StubApplicationValidator,
    StubDeterministicParser,
)
from housing_processor.infrastructure.excel import OpenpyxlExcelRenderer
from housing_processor.infrastructure.integrations.supabase_client import create_supabase_client
from housing_processor.infrastructure.llm import (
    NoOpLlmStructuredExtractor,
    ReviewRequiredGroupMatcher,
    StubIdentityResolver,
)
from housing_processor.infrastructure.storage import LocalFileStorage
from housing_processor.infrastructure.support import SystemClock, UuidIdGenerator

if TYPE_CHECKING:
    from supabase import Client


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    uow_factory: SqlAlchemyUnitOfWorkFactory
    storage: LocalFileStorage
    ingest_handler: IngestApplicationHandler
    process_handler: ProcessApplicationHandler
    excel_renderer: OpenpyxlExcelRenderer
    clock: SystemClock
    id_generator: UuidIdGenerator
    supabase_client: Client | None


def build_container(settings: Settings | None = None) -> AppContainer:
    settings = settings or get_settings()
    engine = create_engine_from_url(settings.database_url.get_secret_value())
    session_factory = create_session_factory(engine)
    uow_factory = SqlAlchemyUnitOfWorkFactory(session_factory)

    storage_root = settings.storage_root or Path("./data/storage")
    storage = LocalFileStorage(storage_root)

    clock = SystemClock()
    id_generator = UuidIdGenerator()

    structured_extractor = (
        NoOpLlmStructuredExtractor()
        if not settings.llm_enabled
        else PassThroughStructuredExtractor()
    )

    ingest_handler = IngestApplicationHandler(
        uow_factory=uow_factory,
        storage=storage,
        clock=clock,
        id_generator=id_generator,
    )
    process_handler = ProcessApplicationHandler(
        uow_factory=uow_factory,
        document_reader=PythonDocxDocumentReader(),
        deterministic_parser=StubDeterministicParser(),
        structured_extractor=structured_extractor,
        validator=StubApplicationValidator(),
        identity_resolver=StubIdentityResolver(),
        group_matcher=ReviewRequiredGroupMatcher(),
        storage=storage,
        clock=clock,
    )

    return AppContainer(
        settings=settings,
        uow_factory=uow_factory,
        storage=storage,
        ingest_handler=ingest_handler,
        process_handler=process_handler,
        excel_renderer=OpenpyxlExcelRenderer(),
        clock=clock,
        id_generator=id_generator,
        supabase_client=create_supabase_client(settings),
    )
