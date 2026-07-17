from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from housing_processor.infrastructure.database.base import Base


class PropertyModel(Base):
    __tablename__ = "properties"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(512), nullable=False, unique=True, index=True)
    aliases_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class GroupPropertyPreferenceModel(Base):
    __tablename__ = "group_property_preferences"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    group_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("groups.id"), nullable=False, index=True
    )
    property_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("properties.id"), nullable=True, index=True
    )
    raw_property: Mapped[str] = mapped_column(String(512), nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
