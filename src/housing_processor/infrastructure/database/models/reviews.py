from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from housing_processor.infrastructure.database.base import Base


class ReviewItemModel(Base):
    __tablename__ = "review_items"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    application_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reason_codes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    suggested_group_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    evidence_summary_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
