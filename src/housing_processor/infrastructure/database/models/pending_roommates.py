from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from housing_processor.infrastructure.database.base import Base


class PendingRoommateReferenceModel(Base):
    __tablename__ = "pending_roommate_references"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    source_application_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True
    )
    target_group_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("groups.id"), nullable=True
    )
    full_name_raw: Mapped[str] = mapped_column(String(512), nullable=False)
    full_name_normalized: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    email_original: Mapped[str | None] = mapped_column(String(320), nullable=True)
    email_normalized: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    phone_original: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phone_e164: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    resolved_applicant_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("applicants.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
