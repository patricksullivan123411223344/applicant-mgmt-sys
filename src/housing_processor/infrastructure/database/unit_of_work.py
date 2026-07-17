from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from housing_processor.infrastructure.database.repositories import (
    SqlAlchemyApplicantRepository,
    SqlAlchemyApplicationRepository,
    SqlAlchemyAuditRepository,
    SqlAlchemyGroupRepository,
    SqlAlchemyReviewRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None
        self.applications: SqlAlchemyApplicationRepository
        self.applicants: SqlAlchemyApplicantRepository
        self.groups: SqlAlchemyGroupRepository
        self.reviews: SqlAlchemyReviewRepository
        self.audits: SqlAlchemyAuditRepository

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self.session = self._session_factory()
        self.applications = SqlAlchemyApplicationRepository(self.session)
        self.applicants = SqlAlchemyApplicantRepository(self.session)
        self.groups = SqlAlchemyGroupRepository(self.session)
        self.reviews = SqlAlchemyReviewRepository(self.session)
        self.audits = SqlAlchemyAuditRepository(self.session)
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.session is None:
            return
        if exc_type is not None:
            self.rollback()
        self.session.close()
        self.session = None

    def commit(self) -> None:
        assert self.session is not None
        self.session.commit()

    def rollback(self) -> None:
        assert self.session is not None
        self.session.rollback()


class SqlAlchemyUnitOfWorkFactory:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def __call__(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(self._session_factory)
