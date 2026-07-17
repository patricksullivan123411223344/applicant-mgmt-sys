from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from housing_processor.infrastructure.database.base import Base


class ExcelExportModel(Base):
    __tablename__ = "excel_exports"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    requested_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    include_statuses_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
