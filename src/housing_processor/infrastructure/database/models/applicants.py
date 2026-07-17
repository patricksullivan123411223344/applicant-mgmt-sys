from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from housing_processor.infrastructure.database.base import Base


class ApplicantModel(Base):
    __tablename__ = "applicants"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(256), nullable=False)
    last_name: Mapped[str] = mapped_column(String(256), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    email_original: Mapped[str | None] = mapped_column(String(320), nullable=True)
    email_normalized: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    phone_original: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phone_e164: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    gpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
