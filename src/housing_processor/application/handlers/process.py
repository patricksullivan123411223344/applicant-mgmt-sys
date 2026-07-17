"""Process-application orchestrator (architecture §20).

Phase 1 scaffold: coordinates collaborators; persistence of match/review
decisions is completed in later Phase 1 slices.
"""

from __future__ import annotations

from housing_processor.application.commands.process import ProcessApplicationCommand
from housing_processor.application.dto.processing import ProcessApplicationResult
from housing_processor.application.ports.extractors import (
    ApplicationValidator,
    DeterministicParser,
    DocumentReader,
    StructuredApplicationExtractor,
)
from housing_processor.application.ports.matching import ApplicantIdentityResolver, GroupMatcher
from housing_processor.application.ports.repositories import GroupCandidateQuery, UnitOfWorkFactory
from housing_processor.application.ports.storage import FileStorage
from housing_processor.application.ports.support import Clock
from housing_processor.domain.applications.status_transitions import assert_can_transition
from housing_processor.domain.shared.enums import ApplicationStatus, MatchDecisionType


class ProcessApplicationHandler:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        document_reader: DocumentReader,
        deterministic_parser: DeterministicParser,
        structured_extractor: StructuredApplicationExtractor,
        validator: ApplicationValidator,
        identity_resolver: ApplicantIdentityResolver,
        group_matcher: GroupMatcher,
        storage: FileStorage,
        clock: Clock,
    ) -> None:
        self._uow_factory = uow_factory
        self._document_reader = document_reader
        self._deterministic_parser = deterministic_parser
        self._structured_extractor = structured_extractor
        self._validator = validator
        self._identity_resolver = identity_resolver
        self._group_matcher = group_matcher
        self._storage = storage
        self._clock = clock

    def handle(self, command: ProcessApplicationCommand) -> ProcessApplicationResult:
        # 1. Load the application and verify its current state.
        with self._uow_factory() as uow:
            application = uow.applications.get(command.application_id)

            if not command.force_reprocess:
                assert_can_transition(
                    application.id,
                    application.status,
                    ApplicationStatus.EXTRACTING,
                )

            application.status = ApplicationStatus.EXTRACTING
            uow.applications.save(application)
            uow.commit()
            storage_key = application.storage_key
            application_id = application.id

        # 2. Read the immutable source document.
        source_path = self._storage.resolve_path(storage_key)
        document = self._document_reader.read(source_path)

        # 3. Run deterministic extraction.
        deterministic_result = self._deterministic_parser.parse(document)

        # 4. Optionally run structured LLM extraction (pass-through in Phase 1).
        extracted = self._structured_extractor.extract(document, deterministic_result)

        # 5. Validate and normalize the extracted contract.
        try:
            validated = self._validator.validate(extracted)
        except Exception:
            with self._uow_factory() as uow:
                application = uow.applications.get(application_id)
                application.status = ApplicationStatus.FAILED
                application.failure_reason = "validation_failed"
                uow.applications.save(application)
                uow.commit()
            raise

        with self._uow_factory() as uow:
            application = uow.applications.get(application_id)
            assert_can_transition(
                application.id,
                ApplicationStatus.EXTRACTING,
                ApplicationStatus.EXTRACTED,
            )
            application.status = ApplicationStatus.EXTRACTED
            uow.applications.save(application)

            assert_can_transition(
                application.id,
                ApplicationStatus.EXTRACTED,
                ApplicationStatus.MATCHING,
            )
            application.status = ApplicationStatus.MATCHING
            uow.applications.save(application)
            uow.commit()

        # 6–8. Load candidates, decide, commit review or match.
        with self._uow_factory() as uow:
            resolution = self._identity_resolver.resolve(validated.applicant)
            candidates = uow.groups.find_candidates(GroupCandidateQuery())
            decision = self._group_matcher.match(validated, resolution, candidates)

            application = uow.applications.get(application_id)
            warnings: list[str] = list(application.warnings)

            # Phase 1: automatic matching surfaces review until manual path lands.
            target = ApplicationStatus.REVIEW_REQUIRED
            if decision.decision == MatchDecisionType.REVIEW_REQUIRED:
                warnings.append("Matching deferred to human review (Phase 1 scaffold).")

            assert_can_transition(application.id, ApplicationStatus.MATCHING, target)
            application.status = target
            application.matcher_version = decision.matcher_version
            application.warnings = warnings
            uow.applications.save(application)
            uow.commit()

            # 9. Return a typed result (audit events wired in a later slice).
            return ProcessApplicationResult(
                application_id=application_id,
                status=application.status,
                applicant_id=resolution.applicant_id,
                group_id=None,
                group_number=None,
                review_item_id=None,
                warnings=tuple(warnings),
            )
