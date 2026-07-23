"""Process-application orchestrator (architecture §20)."""

from __future__ import annotations

from uuid import UUID, uuid4

from housing_processor.application.commands.process import ProcessApplicationCommand
from housing_processor.application.dto.processing import ProcessApplicationResult
from housing_processor.application.extraction_snapshot import (
    build_extracted_v1_snapshot,
    replace_extracted_v1_warning,
)
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
from housing_processor.domain.applicants.entities import Applicant
from housing_processor.domain.applications.status_transitions import assert_can_transition
from housing_processor.domain.reviews.entities import ReviewItem
from housing_processor.domain.shared.enums import ApplicationStatus, MatchDecisionType, ReviewStatus
from housing_processor.domain.shared.identifiers import ApplicantId, ReviewItemId
from housing_processor.infrastructure.docx import PARSER_VERSION


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
            original_filename = application.original_filename

        source_path = self._storage.resolve_path(storage_key)
        document = self._document_reader.read(source_path)
        document.source_filename = original_filename

        deterministic_result = self._deterministic_parser.parse(document)
        extracted = self._structured_extractor.extract(document, deterministic_result)

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
            application.parser_version = PARSER_VERSION
            warnings = list(application.warnings)
            warnings.extend(extracted.warnings)
            for issue in validated.issues:
                warnings.append(f"{issue.code}: {issue.message}")
            application.warnings = warnings
            uow.applications.save(application)

            assert_can_transition(
                application.id,
                ApplicationStatus.EXTRACTED,
                ApplicationStatus.MATCHING,
            )
            application.status = ApplicationStatus.MATCHING
            uow.applications.save(application)
            uow.commit()

        with self._uow_factory() as uow:
            resolution = self._identity_resolver.resolve(validated.applicant)
            candidates = uow.groups.find_candidates(GroupCandidateQuery())
            decision = self._group_matcher.match(validated, resolution, candidates)

            application = uow.applications.get(application_id)
            warnings = list(application.warnings)
            now = self._clock.now()

            applicant_id = resolution.applicant_id
            if applicant_id is None:
                for warning in warnings:
                    if warning.startswith("applicant.upserted:"):
                        try:
                            applicant_id = ApplicantId(UUID(warning.split(":", 1)[1]))
                            break
                        except Exception:
                            continue

            if applicant_id is not None:
                try:
                    existing = uow.applicants.get(applicant_id)
                    existing.name = validated.applicant.name
                    existing.email = validated.applicant.email
                    existing.phone = validated.applicant.phone
                    existing.gpa = validated.applicant.gpa
                    existing.version += 1
                    uow.applicants.save(existing)
                except Exception:
                    applicant_id = None

            if applicant_id is None and resolution.is_new:
                applicant_id = ApplicantId(uuid4())
                uow.applicants.add(
                    Applicant(
                        id=applicant_id,
                        name=validated.applicant.name,
                        email=validated.applicant.email,
                        phone=validated.applicant.phone,
                        gpa=validated.applicant.gpa,
                        created_at=now,
                        version=1,
                    )
                )

            if applicant_id is not None:
                tag = f"applicant.upserted:{applicant_id}"
                if tag not in warnings:
                    warnings.append(tag)

            snapshot = build_extracted_v1_snapshot(extracted, validated)
            warnings = replace_extracted_v1_warning(warnings, snapshot)

            roommates = snapshot.get("roommates") or []
            if roommates:
                pending = "|".join(str(name) for name in roommates)
                pending_tag = f"pending_roommates:{pending}"
                warnings = [w for w in warnings if not w.startswith("pending_roommates:")]
                warnings.append(pending_tag)
            else:
                warnings = [w for w in warnings if not w.startswith("pending_roommates:")]

            review_item_id = None
            target = ApplicationStatus.REVIEW_REQUIRED
            if decision.decision == MatchDecisionType.REVIEW_REQUIRED:
                warnings.append("Matching deferred to human review — create or attach a group.")
                review_item_id = ReviewItemId(uuid4())
                uow.reviews.add(
                    ReviewItem(
                        id=review_item_id,
                        application_id=application_id,
                        status=ReviewStatus.OPEN,
                        reason_codes=decision.reason_codes + resolution.reason_codes,
                        created_at=now,
                        suggested_group_id=decision.selected_group_id,
                        evidence_summary=list(decision.reason_codes),
                    )
                )
                application.review_item_id = review_item_id

            assert_can_transition(application.id, ApplicationStatus.MATCHING, target)
            application.status = target
            application.matcher_version = decision.matcher_version
            application.warnings = warnings
            uow.applications.save(application)
            uow.commit()

            return ProcessApplicationResult(
                application_id=application_id,
                status=application.status,
                applicant_id=applicant_id,
                group_id=None,
                group_number=None,
                review_item_id=review_item_id,
                warnings=tuple(warnings),
            )
