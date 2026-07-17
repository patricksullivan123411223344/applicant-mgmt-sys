"""Initial Phase 1 schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-17
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("duplicate_of_application_id", sa.Uuid(), nullable=True),
        sa.Column("group_id", sa.Uuid(), nullable=True),
        sa.Column("review_item_id", sa.Uuid(), nullable=True),
        sa.Column("parser_version", sa.String(length=64), nullable=True),
        sa.Column("matcher_version", sa.String(length=64), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("warnings_json", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_hash"),
    )
    op.create_index("ix_applications_file_hash", "applications", ["file_hash"])
    op.create_index("ix_applications_status", "applications", ["status"])
    op.create_index("ix_applications_group_id", "applications", ["group_id"])
    op.create_index("ix_applications_idempotency_key", "applications", ["idempotency_key"])

    op.create_table(
        "applicants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("first_name", sa.String(length=256), nullable=False),
        sa.Column("last_name", sa.String(length=256), nullable=False),
        sa.Column("normalized_name", sa.String(length=512), nullable=False),
        sa.Column("email_original", sa.String(length=320), nullable=True),
        sa.Column("email_normalized", sa.String(length=320), nullable=True),
        sa.Column("phone_original", sa.String(length=64), nullable=True),
        sa.Column("phone_e164", sa.String(length=32), nullable=True),
        sa.Column("gpa", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_applicants_normalized_name", "applicants", ["normalized_name"])
    op.create_index("ix_applicants_email_normalized", "applicants", ["email_normalized"])
    op.create_index("ix_applicants_phone_e164", "applicants", ["phone_e164"])

    op.create_table(
        "groups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("group_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("first_application_received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_number"),
    )
    op.create_index("ix_groups_group_number", "groups", ["group_number"])
    op.create_index("ix_groups_status", "groups", ["status"])

    op.create_table(
        "group_number_seq",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("next_value", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("INSERT INTO group_number_seq (id, next_value) VALUES (1, 1)")

    op.create_table(
        "group_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("applicant_id", sa.Uuid(), nullable=False),
        sa.Column("is_contact", sa.Boolean(), nullable=False),
        sa.Column("match_method", sa.String(length=64), nullable=False),
        sa.Column("match_confidence", sa.Float(), nullable=False),
        sa.Column("source_application_id", sa.Uuid(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["applicant_id"], ["applicants.id"]),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "applicant_id", name="uq_group_applicant"),
    )
    op.create_index("ix_group_members_group_id", "group_members", ["group_id"])
    op.create_index("ix_group_members_applicant_id", "group_members", ["applicant_id"])

    op.create_table(
        "review_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("reason_codes_json", sa.Text(), nullable=False),
        sa.Column("suggested_group_id", sa.Uuid(), nullable=True),
        sa.Column("evidence_summary_json", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.Uuid(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_items_application_id", "review_items", ["application_id"])
    op.create_index("ix_review_items_status", "review_items", ["status"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_occurred_at", "audit_events", ["occurred_at"])
    op.create_index("ix_audit_events_request_id", "audit_events", ["request_id"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])

    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outbox_events_event_type", "outbox_events", ["event_type"])
    op.create_index("ix_outbox_events_aggregate_id", "outbox_events", ["aggregate_id"])


def downgrade() -> None:
    op.drop_table("outbox_events")
    op.drop_table("audit_events")
    op.drop_table("review_items")
    op.drop_table("group_members")
    op.drop_table("group_number_seq")
    op.drop_table("groups")
    op.drop_table("applicants")
    op.drop_table("applications")
