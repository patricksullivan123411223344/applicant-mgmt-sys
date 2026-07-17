"""Ingest an uploaded DOCX: hash, store, create application record."""

from __future__ import annotations

import hashlib

from housing_processor.application.commands.ingest import IngestApplicationCommand
from housing_processor.application.ports.repositories import UnitOfWorkFactory
from housing_processor.application.ports.storage import FileStorage
from housing_processor.application.ports.support import Clock, IdGenerator
from housing_processor.domain.applications.entities import ApplicationRecord
from housing_processor.domain.shared.enums import ApplicationStatus
from housing_processor.domain.shared.identifiers import ApplicationId


class IngestApplicationResult:
    def __init__(
        self,
        application_id: ApplicationId,
        status: ApplicationStatus,
        duplicate_of_application_id: ApplicationId | None,
        received_at: object,
    ) -> None:
        self.application_id = application_id
        self.status = status
        self.duplicate_of_application_id = duplicate_of_application_id
        self.received_at = received_at


class IngestApplicationHandler:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        storage: FileStorage,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._uow_factory = uow_factory
        self._storage = storage
        self._clock = clock
        self._id_generator = id_generator

    def handle(self, command: IngestApplicationCommand) -> IngestApplicationResult:
        file_hash = hashlib.sha256(command.content).hexdigest()
        received_at = command.received_at or self._clock.now()

        with self._uow_factory() as uow:
            existing = uow.applications.find_by_file_hash(file_hash)
            if existing is not None:
                return IngestApplicationResult(
                    application_id=existing.id,
                    status=ApplicationStatus.DUPLICATE,
                    duplicate_of_application_id=existing.id,
                    received_at=existing.received_at,
                )

            stored = self._storage.save_source(command.content, command.filename)
            application_id = ApplicationId(self._id_generator.new_uuid())
            record = ApplicationRecord(
                id=application_id,
                file_hash=file_hash,
                original_filename=command.filename,
                storage_key=stored.storage_key,
                status=ApplicationStatus.RECEIVED,
                received_at=received_at,
                source=command.source,
                idempotency_key=command.idempotency_key,
                created_by=command.actor.actor_id,
            )
            uow.applications.add(record)
            uow.commit()

            return IngestApplicationResult(
                application_id=application_id,
                status=ApplicationStatus.RECEIVED,
                duplicate_of_application_id=None,
                received_at=received_at,
            )
