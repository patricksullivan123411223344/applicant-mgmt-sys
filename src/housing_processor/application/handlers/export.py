"""Excel export from database groups/members."""

from __future__ import annotations

import json
from datetime import timezone
from uuid import uuid4

from housing_processor.application.commands.export import CreateExcelExportCommand
from housing_processor.application.contracts.excel import (
    HousingWorkbookProjection,
    WorkbookApplicantRow,
)
from housing_processor.application.extraction_snapshot import (
    parse_extracted_v1_snapshot,
    property_prefs_from_snapshot,
)
from housing_processor.application.ports.repositories import UnitOfWorkFactory
from housing_processor.application.ports.storage import ExcelRenderer, FileStorage
from housing_processor.application.ports.support import Clock
from housing_processor.infrastructure.database.models.exports import ExcelExportModel


class CreateExcelExportHandler:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        storage: FileStorage,
        excel_renderer: ExcelRenderer,
        clock: Clock,
    ) -> None:
        self._uow_factory = uow_factory
        self._storage = storage
        self._excel_renderer = excel_renderer
        self._clock = clock

    def handle(self, command: CreateExcelExportCommand) -> tuple[str, str]:
        """Returns (export_id, status)."""
        export_id = uuid4()
        now = self._clock.now()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        with self._uow_factory() as uow:
            groups, _ = uow.groups.list(limit=10_000, offset=0)
            rows: list[WorkbookApplicantRow] = []
            for group in groups:
                for member in group.members:
                    applicant = uow.applicants.get(member.applicant_id)
                    name = f"{applicant.name.first} {applicant.name.last}".strip()
                    received = None
                    prefs: list[str] = []
                    try:
                        app = uow.applications.get(member.source_application_id)
                        received = app.received_at.date()
                        prefs = property_prefs_from_snapshot(
                            parse_extracted_v1_snapshot(app.warnings)
                        )
                    except Exception:
                        received = None
                        prefs = []
                    rows.append(
                        WorkbookApplicantRow(
                            group_number=group.group_number,
                            applicant_name=name,
                            is_contact=member.is_contact,
                            phone=applicant.phone.original if applicant.phone else None,
                            email=applicant.email.original if applicant.email else None,
                            gpa=applicant.gpa,
                            requested_properties=prefs,
                            expected_group_size=len(group.members),
                            application_received_date=received,
                            group_status=group.status.value,
                            review_notes=None,
                        )
                    )

            projection = HousingWorkbookProjection(
                generated_at=now,
                export_id=export_id,
                rows=rows,
            )
            content = self._excel_renderer.render(projection)
            stored = self._storage.save_export(content, f"housing-export-{export_id.hex}.xlsx")

            assert uow.session is not None
            uow.session.add(
                ExcelExportModel(
                    id=export_id,
                    status="completed",
                    storage_key=stored.storage_key,
                    requested_by=command.actor.actor_id,
                    request_id=command.actor.request_id,
                    include_statuses_json=json.dumps(
                        [s.value for s in command.include_group_statuses]
                    ),
                    error_message=None,
                    created_at=now,
                    completed_at=now,
                )
            )
            uow.commit()

        return str(export_id), "completed"
