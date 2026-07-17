from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from housing_processor.infrastructure.database.base import Base


class ApplicationModel(Base):
    __tablename__ = "applications"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="manual_upload")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    duplicate_of_application_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    group_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    review_item_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    parser_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    matcher_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
