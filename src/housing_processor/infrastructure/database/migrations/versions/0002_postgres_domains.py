"""Add documented domains + Postgres group_number sequence.

Revision ID: 0002_postgres_domains
Revises: 0001_initial
Create Date: 2026-07-17
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_postgres_domains"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Pending roommate references (PROJECT_OVERVIEW)
    op.create_table(
        "pending_roommate_references",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_application_id", sa.Uuid(), nullable=False),
        sa.Column("target_group_id", sa.Uuid(), nullable=True),
        sa.Column("full_name_raw", sa.String(length=512), nullable=False),
        sa.Column("full_name_normalized", sa.String(length=512), nullable=False),
        sa.Column("email_original", sa.String(length=320), nullable=True),
        sa.Column("email_normalized", sa.String(length=320), nullable=True),
        sa.Column("phone_original", sa.String(length=64), nullable=True),
        sa.Column("phone_e164", sa.String(length=32), nullable=True),
        sa.Column("resolved_applicant_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["source_application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["target_group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["resolved_applicant_id"], ["applicants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_pending_roommate_refs_source_app",
        "pending_roommate_references",
        ["source_application_id"],
    )
    op.create_index(
        "ix_pending_roommate_refs_normalized_name",
        "pending_roommate_references",
        ["full_name_normalized"],
    )
    op.create_index(
        "ix_pending_roommate_refs_email",
        "pending_roommate_references",
        ["email_normalized"],
    )
    op.create_index(
        "ix_pending_roommate_refs_phone",
        "pending_roommate_references",
        ["phone_e164"],
    )
    op.create_index(
        "ix_pending_roommate_refs_status",
        "pending_roommate_references",
        ["status"],
    )

    # Properties
    op.create_table(
        "properties",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("normalized_name", sa.String(length=512), nullable=False),
        sa.Column("aliases_json", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_name", name="uq_properties_normalized_name"),
    )
    op.create_index("ix_properties_normalized_name", "properties", ["normalized_name"])

    # Group property preferences
    op.create_table(
        "group_property_preferences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("property_id", sa.Uuid(), nullable=True),
        sa.Column("raw_property", sa.String(length=512), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_group_property_prefs_group_id",
        "group_property_preferences",
        ["group_id"],
    )
    op.create_index(
        "ix_group_property_prefs_property_id",
        "group_property_preferences",
        ["property_id"],
    )

    # Excel export history
    op.create_table(
        "excel_exports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=True),
        sa.Column("requested_by", sa.Uuid(), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("include_statuses_json", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_excel_exports_status", "excel_exports", ["status"])
    op.create_index("ix_excel_exports_created_at", "excel_exports", ["created_at"])

    # ARCH §21: real Postgres SEQUENCE; keep SQLite table allocator locally.
    if dialect == "postgresql":
        # Capture current next value from the SQLite-style table if present.
        next_value = 1
        try:
            result = bind.execute(sa.text("SELECT next_value FROM group_number_seq WHERE id = 1"))
            row = result.first()
            if row is not None:
                next_value = int(row[0])
        except Exception:
            next_value = 1

        op.execute(sa.text("DROP TABLE IF EXISTS group_number_seq"))
        op.execute(
            sa.text(f"CREATE SEQUENCE IF NOT EXISTS group_number_seq START WITH {next_value} INCREMENT BY 1")
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute(sa.text("DROP SEQUENCE IF EXISTS group_number_seq"))
        op.create_table(
            "group_number_seq",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("next_value", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.execute(sa.text("INSERT INTO group_number_seq (id, next_value) VALUES (1, 1)"))

    op.drop_index("ix_excel_exports_created_at", table_name="excel_exports")
    op.drop_index("ix_excel_exports_status", table_name="excel_exports")
    op.drop_table("excel_exports")

    op.drop_index("ix_group_property_prefs_property_id", table_name="group_property_preferences")
    op.drop_index("ix_group_property_prefs_group_id", table_name="group_property_preferences")
    op.drop_table("group_property_preferences")

    op.drop_index("ix_properties_normalized_name", table_name="properties")
    op.drop_table("properties")

    op.drop_index("ix_pending_roommate_refs_status", table_name="pending_roommate_references")
    op.drop_index("ix_pending_roommate_refs_phone", table_name="pending_roommate_references")
    op.drop_index("ix_pending_roommate_refs_email", table_name="pending_roommate_references")
    op.drop_index(
        "ix_pending_roommate_refs_normalized_name",
        table_name="pending_roommate_references",
    )
    op.drop_index("ix_pending_roommate_refs_source_app", table_name="pending_roommate_references")
    op.drop_table("pending_roommate_references")
