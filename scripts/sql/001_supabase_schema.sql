-- ============================================================================
-- Student Housing Application Processing System
-- Postgres / Supabase DDL aligned with PROJECT_OVERVIEW core data domains
-- and SYSTEM_ARCHITECTURE (sequence, outbox, optimistic version).
--
-- Preferred apply path:  uv run alembic upgrade head
-- Manual apply: paste into Supabase SQL Editor, then:
--   uv run alembic stamp head
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Application files (PROJECT_OVERVIEW: Application files)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    original_filename VARCHAR(512) NOT NULL,
    storage_key VARCHAR(1024) NOT NULL,
    status VARCHAR(64) NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    source VARCHAR(64) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    duplicate_of_application_id UUID NULL,
    group_id UUID NULL,
    review_item_id UUID NULL,
    parser_version VARCHAR(64) NULL,
    matcher_version VARCHAR(64) NULL,
    failure_reason TEXT NULL,
    warnings_json TEXT NOT NULL DEFAULT '[]',
    idempotency_key VARCHAR(128) NULL,
    created_by UUID NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_applications_file_hash ON applications (file_hash);
CREATE INDEX IF NOT EXISTS ix_applications_status ON applications (status);
CREATE INDEX IF NOT EXISTS ix_applications_group_id ON applications (group_id);
CREATE INDEX IF NOT EXISTS ix_applications_idempotency_key ON applications (idempotency_key);

-- ---------------------------------------------------------------------------
-- Applicants (PROJECT_OVERVIEW: Applicants)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS applicants (
    id UUID PRIMARY KEY,
    first_name VARCHAR(256) NOT NULL,
    last_name VARCHAR(256) NOT NULL,
    normalized_name VARCHAR(512) NOT NULL,
    email_original VARCHAR(320) NULL,
    email_normalized VARCHAR(320) NULL,
    phone_original VARCHAR(64) NULL,
    phone_e164 VARCHAR(32) NULL,
    gpa NUMERIC(4, 2) NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_applicants_normalized_name ON applicants (normalized_name);
CREATE INDEX IF NOT EXISTS ix_applicants_email_normalized ON applicants (email_normalized);
CREATE INDEX IF NOT EXISTS ix_applicants_phone_e164 ON applicants (phone_e164);

-- ---------------------------------------------------------------------------
-- Roommate groups (PROJECT_OVERVIEW: Roommate groups)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS groups (
    id UUID PRIMARY KEY,
    group_number INTEGER NOT NULL UNIQUE,
    status VARCHAR(64) NOT NULL,
    first_application_received_at TIMESTAMPTZ NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_groups_group_number ON groups (group_number);
CREATE INDEX IF NOT EXISTS ix_groups_status ON groups (status);

-- ---------------------------------------------------------------------------
-- Permanent sequential group numbers (SYSTEM_ARCHITECTURE §21)
-- Postgres SEQUENCE — never allocate via MAX(group_number)+1 in app code.
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS group_number_seq START WITH 1 INCREMENT BY 1;

-- ---------------------------------------------------------------------------
-- Group memberships (PROJECT_OVERVIEW: Group memberships)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS group_members (
    id UUID PRIMARY KEY,
    group_id UUID NOT NULL REFERENCES groups (id),
    applicant_id UUID NOT NULL REFERENCES applicants (id),
    is_contact BOOLEAN NOT NULL DEFAULT FALSE,
    match_method VARCHAR(64) NOT NULL,
    match_confidence DOUBLE PRECISION NOT NULL,
    source_application_id UUID NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_group_applicant UNIQUE (group_id, applicant_id)
);

CREATE INDEX IF NOT EXISTS ix_group_members_group_id ON group_members (group_id);
CREATE INDEX IF NOT EXISTS ix_group_members_applicant_id ON group_members (applicant_id);

-- ---------------------------------------------------------------------------
-- Pending roommate references (PROJECT_OVERVIEW: Pending roommate references)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pending_roommate_references (
    id UUID PRIMARY KEY,
    source_application_id UUID NOT NULL REFERENCES applications (id),
    target_group_id UUID NULL REFERENCES groups (id),
    full_name_raw VARCHAR(512) NOT NULL,
    full_name_normalized VARCHAR(512) NOT NULL,
    email_original VARCHAR(320) NULL,
    email_normalized VARCHAR(320) NULL,
    phone_original VARCHAR(64) NULL,
    phone_e164 VARCHAR(32) NULL,
    resolved_applicant_id UUID NULL REFERENCES applicants (id),
    status VARCHAR(64) NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_pending_roommate_refs_source_app
    ON pending_roommate_references (source_application_id);
CREATE INDEX IF NOT EXISTS ix_pending_roommate_refs_normalized_name
    ON pending_roommate_references (full_name_normalized);
CREATE INDEX IF NOT EXISTS ix_pending_roommate_refs_email
    ON pending_roommate_references (email_normalized);
CREATE INDEX IF NOT EXISTS ix_pending_roommate_refs_phone
    ON pending_roommate_references (phone_e164);
CREATE INDEX IF NOT EXISTS ix_pending_roommate_refs_status
    ON pending_roommate_references (status);

-- ---------------------------------------------------------------------------
-- Properties (PROJECT_OVERVIEW: Properties)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS properties (
    id UUID PRIMARY KEY,
    name VARCHAR(512) NOT NULL,
    normalized_name VARCHAR(512) NOT NULL,
    aliases_json TEXT NOT NULL DEFAULT '[]',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_properties_normalized_name
    ON properties (normalized_name);

-- ---------------------------------------------------------------------------
-- Group property preferences (PROJECT_OVERVIEW: Group property preferences)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS group_property_preferences (
    id UUID PRIMARY KEY,
    group_id UUID NOT NULL REFERENCES groups (id),
    property_id UUID NULL REFERENCES properties (id),
    raw_property VARCHAR(512) NOT NULL,
    rank INTEGER NULL,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_group_property_prefs_group_id
    ON group_property_preferences (group_id);
CREATE INDEX IF NOT EXISTS ix_group_property_prefs_property_id
    ON group_property_preferences (property_id);

-- ---------------------------------------------------------------------------
-- Review items (PROJECT_OVERVIEW: Review items)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review_items (
    id UUID PRIMARY KEY,
    application_id UUID NOT NULL,
    status VARCHAR(64) NOT NULL,
    reason_codes_json TEXT NOT NULL DEFAULT '[]',
    suggested_group_id UUID NULL,
    evidence_summary_json TEXT NOT NULL DEFAULT '[]',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ NULL,
    resolved_by UUID NULL,
    resolution_notes TEXT NULL
);

CREATE INDEX IF NOT EXISTS ix_review_items_application_id ON review_items (application_id);
CREATE INDEX IF NOT EXISTS ix_review_items_status ON review_items (status);

-- ---------------------------------------------------------------------------
-- Audit events (PROJECT_OVERVIEW: Audit events; ARCH §3.6)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(128) NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    actor_id UUID NULL,
    request_id VARCHAR(128) NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS ix_audit_events_event_type ON audit_events (event_type);
CREATE INDEX IF NOT EXISTS ix_audit_events_occurred_at ON audit_events (occurred_at);
CREATE INDEX IF NOT EXISTS ix_audit_events_request_id ON audit_events (request_id);
CREATE INDEX IF NOT EXISTS ix_audit_events_entity_id ON audit_events (entity_id);

-- ---------------------------------------------------------------------------
-- Transactional outbox (SYSTEM_ARCHITECTURE §22)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS outbox_events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(128) NOT NULL,
    aggregate_type VARCHAR(64) NOT NULL,
    aggregate_id VARCHAR(64) NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ NULL,
    attempt INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_outbox_events_event_type ON outbox_events (event_type);
CREATE INDEX IF NOT EXISTS ix_outbox_events_aggregate_id ON outbox_events (aggregate_id);
CREATE INDEX IF NOT EXISTS ix_outbox_events_processed_at ON outbox_events (processed_at);

-- ---------------------------------------------------------------------------
-- Excel export history (PROJECT_OVERVIEW: Excel export history)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS excel_exports (
    id UUID PRIMARY KEY,
    status VARCHAR(64) NOT NULL,
    storage_key VARCHAR(1024) NULL,
    requested_by UUID NULL,
    request_id VARCHAR(128) NULL,
    include_statuses_json TEXT NOT NULL DEFAULT '[]',
    error_message TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_excel_exports_status ON excel_exports (status);
CREATE INDEX IF NOT EXISTS ix_excel_exports_created_at ON excel_exports (created_at);
