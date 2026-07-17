"""Synchronous outbox processor for Phase 1 MVP (architecture §22)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from housing_processor.infrastructure.database.models.outbox import OutboxEventModel


class SynchronousOutboxProcessor:
    """Marks pending outbox events as processed in-process.

    Future workers will publish or handle these events asynchronously.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def process_pending(self, *, limit: int = 100) -> int:
        stmt = (
            select(OutboxEventModel)
            .where(OutboxEventModel.processed_at.is_(None))
            .order_by(OutboxEventModel.created_at)
            .limit(limit)
        )
        events = list(self._session.scalars(stmt).all())
        now = datetime.now(timezone.utc)
        for event in events:
            event.processed_at = now
            event.attempt += 1
        self._session.commit()
        return len(events)
