"""Add durable BE1 organization, classroom, consent, session and lifecycle records."""

from __future__ import annotations

from alembic import op

revision = "20261014_0002"
down_revision = "20261014_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    ddl = """
        CREATE TABLE be1_organizations (
            organization_id varchar(128) PRIMARY KEY,
            display_name varchar(200) NOT NULL,
            state varchar(24) NOT NULL DEFAULT 'active',
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE TABLE be1_adult_identities (
            subject varchar(256) PRIMARY KEY,
            issuer varchar(512) NOT NULL,
            state varchar(24) NOT NULL DEFAULT 'active',
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE TABLE be1_organization_assignments (
            assignment_id varchar(36) PRIMARY KEY,
            organization_id varchar(128) NOT NULL REFERENCES be1_organizations ON DELETE RESTRICT,
            subject varchar(256) NOT NULL REFERENCES be1_adult_identities ON DELETE RESTRICT,
            class_id varchar(128),
            role varchar(32) NOT NULL CHECK (role IN ('school_admin','teacher','guide','observer')),
            active boolean NOT NULL DEFAULT true,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_be1_assignment UNIQUE (organization_id, subject, class_id, role)
        );
        CREATE INDEX ix_be1_assignment_subject
          ON be1_organization_assignments(subject, organization_id);

        CREATE TABLE be1_classrooms (
            class_id varchar(128) PRIMARY KEY,
            organization_id varchar(128) NOT NULL REFERENCES be1_organizations ON DELETE RESTRICT,
            display_name varchar(200) NOT NULL,
            state varchar(24) NOT NULL DEFAULT 'active',
            created_by varchar(256) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_be1_class_org UNIQUE (organization_id, class_id)
        );
        CREATE INDEX ix_be1_class_org_state ON be1_classrooms(organization_id, state);

        CREATE TABLE be1_managed_profiles (
            child_id varchar(128) PRIMARY KEY,
            organization_id varchar(128) NOT NULL REFERENCES be1_organizations ON DELETE RESTRICT,
            class_id varchar(128) NOT NULL REFERENCES be1_classrooms ON DELETE RESTRICT,
            display_name varchar(200) NOT NULL,
            age_months integer NOT NULL CHECK (age_months BETWEEN 36 AND 155),
            consent_id varchar(36) NOT NULL,
            consent_purpose_ref varchar(128) NOT NULL,
            state varchar(24) NOT NULL DEFAULT 'active',
            created_by varchar(256) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_be1_profile_org_child UNIQUE (organization_id, child_id)
        );
        CREATE INDEX ix_be1_profile_org_class ON be1_managed_profiles(organization_id, class_id);

        CREATE TABLE be1_enrollments (
            enrollment_id varchar(36) PRIMARY KEY,
            organization_id varchar(128) NOT NULL,
            class_id varchar(128) NOT NULL,
            child_id varchar(128) NOT NULL,
            state varchar(24) NOT NULL DEFAULT 'active' CHECK (state IN ('active','withdrawn')),
            created_by varchar(256) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_be1_enrollment UNIQUE (organization_id, class_id, child_id)
        );

        CREATE TABLE be1_consent_records (
            consent_id varchar(36) PRIMARY KEY,
            organization_id varchar(128) NOT NULL,
            class_id varchar(128) NOT NULL,
            child_id varchar(128) NOT NULL,
            purpose_ref varchar(128) NOT NULL,
            evidence_ref varchar(512),
            state varchar(24) NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','revoked')),
            recorded_by varchar(256) NOT NULL,
            recorded_at timestamptz NOT NULL DEFAULT now(),
            verification_note text
        );
        CREATE INDEX ix_be1_consent_child ON be1_consent_records(organization_id, child_id, state);

        CREATE TABLE be1_sessions (
            session_id varchar(128) PRIMARY KEY,
            organization_id varchar(128) NOT NULL,
            class_id varchar(128) NOT NULL,
            created_by varchar(256) NOT NULL,
            state varchar(24) NOT NULL DEFAULT 'configured'
              CHECK (state IN ('configured','lobby','active','paused','finished')),
            revision integer NOT NULL DEFAULT 1 CHECK (revision > 0),
            configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
            active_phase varchar(64) NOT NULL DEFAULT 'lobby',
            started_at timestamptz,
            ended_at timestamptz,
            retain_until timestamptz,
            retention_enqueued_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_be1_session_class_state ON be1_sessions(organization_id, class_id, state);

        CREATE TABLE be1_device_grants (
            grant_id varchar(36) PRIMARY KEY,
            organization_id varchar(128) NOT NULL,
            session_id varchar(128) NOT NULL,
            device_key_hash varchar(64) NOT NULL,
            state varchar(24) NOT NULL DEFAULT 'pending'
              CHECK (state IN ('pending','admitted','revoked')),
            requested_by varchar(256) NOT NULL,
            admitted_child_id varchar(128),
            admitted_by varchar(256),
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_be1_device_session_state
          ON be1_device_grants(organization_id, session_id, state);

        CREATE TABLE be1_session_memberships (
            membership_id varchar(36) PRIMARY KEY,
            organization_id varchar(128) NOT NULL,
            session_id varchar(128) NOT NULL,
            class_id varchar(128) NOT NULL,
            child_id varchar(128) NOT NULL,
            state varchar(24) NOT NULL DEFAULT 'join_pending'
              CHECK (state IN ('join_pending','admitted','left','removed')),
            group_id varchar(128),
            device_grant_id varchar(36),
            progress varchar(32) NOT NULL DEFAULT 'not_started',
            help_requested boolean NOT NULL DEFAULT false,
            requested_at timestamptz NOT NULL DEFAULT now(),
            admitted_at timestamptz,
            CONSTRAINT uq_be1_membership UNIQUE (organization_id, session_id, child_id)
        );
        CREATE INDEX ix_be1_membership_session
          ON be1_session_memberships(organization_id, session_id, state);

        CREATE TABLE be1_session_groups (
            group_id varchar(128) PRIMARY KEY,
            organization_id varchar(128) NOT NULL,
            session_id varchar(128) NOT NULL,
            display_name varchar(120) NOT NULL,
            state varchar(24) NOT NULL DEFAULT 'active'
              CHECK (state IN ('active','locked','archived')),
            created_by varchar(256) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_be1_group UNIQUE (organization_id, session_id, group_id)
        );

        CREATE TABLE be1_child_turns (
            turn_id varchar(36) PRIMARY KEY,
            organization_id varchar(128) NOT NULL,
            session_id varchar(128) NOT NULL,
            child_id varchar(128) NOT NULL,
            group_id varchar(128) NOT NULL,
            canvas_id varchar(128) NOT NULL,
            document_epoch integer NOT NULL DEFAULT 1 CHECK (document_epoch > 0),
            device_grant_id varchar(36) NOT NULL,
            state varchar(24) NOT NULL DEFAULT 'active'
              CHECK (state IN ('active','closed','revoked')),
            created_by varchar(256) NOT NULL,
            started_at timestamptz NOT NULL DEFAULT now(),
            ended_at timestamptz
        );
        CREATE INDEX ix_be1_turn_session_state
          ON be1_child_turns(organization_id, session_id, state);

        CREATE TABLE be1_gallery_snapshots (
            gallery_id varchar(128) PRIMARY KEY,
            organization_id varchar(128) NOT NULL,
            session_id varchar(128) NOT NULL,
            artifact_ref varchar(256) NOT NULL,
            audience varchar(64) NOT NULL,
            contributor_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
            caption varchar(500),
            annotations jsonb NOT NULL DEFAULT '[]'::jsonb,
            state varchar(24) NOT NULL DEFAULT 'draft'
              CHECK (state IN ('draft','published','recalled')),
            created_by varchar(256) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_be1_gallery_org_state ON be1_gallery_snapshots(organization_id, state);

        CREATE TABLE be1_observations (
            observation_id varchar(36) PRIMARY KEY,
            organization_id varchar(128) NOT NULL,
            session_id varchar(128) NOT NULL,
            child_id varchar(128) NOT NULL,
            kind varchar(32) NOT NULL,
            content jsonb NOT NULL,
            source_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
            created_by varchar(256) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_be1_observation_child
          ON be1_observations(organization_id, child_id, created_at);

        CREATE TABLE be1_data_lifecycle_requests (
            request_id varchar(36) PRIMARY KEY,
            organization_id varchar(128) NOT NULL,
            request_type varchar(24) NOT NULL,
            target_ref varchar(256) NOT NULL,
            state varchar(32) NOT NULL DEFAULT 'requested'
              CHECK (state IN (
                'requested','running','awaiting_external_purge','completed','exception'
              )),
            unresolved_items integer NOT NULL DEFAULT 0 CHECK (unresolved_items >= 0),
            result_ref varchar(512),
            requested_by varchar(256) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            completed_at timestamptz
        );
        CREATE INDEX ix_be1_data_request_org_state
          ON be1_data_lifecycle_requests(organization_id, state);
        """
    for statement in ddl.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    for table in (
        "be1_data_lifecycle_requests",
        "be1_observations",
        "be1_gallery_snapshots",
        "be1_child_turns",
        "be1_session_groups",
        "be1_session_memberships",
        "be1_device_grants",
        "be1_sessions",
        "be1_consent_records",
        "be1_enrollments",
        "be1_managed_profiles",
        "be1_classrooms",
        "be1_organization_assignments",
        "be1_adult_identities",
        "be1_organizations",
    ):
        op.execute(f"DROP TABLE {table}")
