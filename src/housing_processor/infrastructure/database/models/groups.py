from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from housing_processor.infrastructure.database.base import Base


class GroupModel(Base):
    __tablename__ = "groups"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    # SQLite MVP: autoincrement allocation via group_number_seq table / identity column.
    # Application code must never compute MAX(group_number) + 1.
    group_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    first_application_received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class GroupMemberModel(Base):
    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "applicant_id", name="uq_group_applicant"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    group_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("groups.id"), nullable=False, index=True
    )
    applicant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("applicants.id"), nullable=False, index=True
    )
    is_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    match_method: Mapped[str] = mapped_column(String(64), nullable=False)
    match_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source_application_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class GroupNumberSequenceModel(Base):
    """Single-row allocator for permanent sequential group numbers (SQLite-safe)."""

    __tablename__ = "group_number_seq"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    next_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
