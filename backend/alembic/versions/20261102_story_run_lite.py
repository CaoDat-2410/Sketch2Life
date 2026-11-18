"""Add the isolated StoryRun-lite Core/Story slice and typed asset ownership."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261102_story_run_lite"
down_revision = None
branch_labels = ("story_run_lite",)
depends_on = ("20261102_pv_0001",)


def upgrade() -> None:
    # Pilot Vision's dependency places the existing Core asset table and A1 ledger before this
    # additive branch. No A2 or application database is used by this migration.
    op.alter_column(
        "core_asset_metadata", "organization_id", existing_type=sa.String(128), nullable=True
    )
    op.add_column(
        "core_asset_metadata",
        sa.Column(
            "owner_scope_kind",
            sa.String(32),
            server_default=sa.text("'ORGANIZATION'"),
            nullable=False,
        ),
    )
    op.add_column(
        "core_asset_metadata", sa.Column("owner_scope_ref", sa.String(128), nullable=True)
    )
    op.create_check_constraint(
        "ck_core_asset_owner_scope",
        "core_asset_metadata",
        "(owner_scope_kind = 'PARENT_ACCOUNT' AND owner_scope_ref IS NOT NULL "
        "AND length(owner_scope_ref) > 0 AND organization_id IS NULL) OR "
        "(owner_scope_kind = 'ORGANIZATION' AND organization_id IS NOT NULL "
        "AND (owner_scope_ref IS NULL OR "
        "(length(owner_scope_ref) > 0 AND owner_scope_ref = organization_id)))",
    )
    op.create_index(
        "ix_core_asset_typed_owner",
        "core_asset_metadata",
        ["owner_scope_kind", "owner_scope_ref", "asset_ref"],
        unique=False,
        postgresql_where=sa.text("owner_scope_ref IS NOT NULL"),
    )
    op.execute(
        sa.text(
            """
            CREATE FUNCTION core_asset_metadata_owner_scope_guard()
            RETURNS trigger AS $$
            BEGIN
              IF NEW.owner_scope_kind = 'ORGANIZATION' THEN
                IF NEW.organization_id IS NULL THEN
                  RAISE EXCEPTION 'organization asset scope requires organization_id'
                    USING ERRCODE = '23514';
                END IF;
                IF NEW.owner_scope_ref IS NULL OR length(NEW.owner_scope_ref) = 0 THEN
                  IF TG_OP = 'UPDATE'
                    AND OLD.owner_scope_kind = 'ORGANIZATION'
                    AND OLD.owner_scope_ref IS NULL
                    AND OLD.organization_id = NEW.organization_id THEN
                    RETURN NEW;
                  END IF;
                  RAISE EXCEPTION 'new organization asset rows require owner_scope_ref'
                    USING ERRCODE = '23514';
                END IF;
                IF NEW.owner_scope_ref <> NEW.organization_id THEN
                  RAISE EXCEPTION 'organization owner scope must match organization_id'
                    USING ERRCODE = '23514';
                END IF;
              ELSIF NEW.owner_scope_kind = 'PARENT_ACCOUNT' THEN
                IF NEW.organization_id IS NOT NULL
                  OR NEW.owner_scope_ref IS NULL
                  OR length(NEW.owner_scope_ref) = 0 THEN
                  RAISE EXCEPTION 'Parent scope requires a typed ref and no organization_id'
                    USING ERRCODE = '23514';
                END IF;
              ELSE
                RAISE EXCEPTION 'unsupported asset owner scope kind' USING ERRCODE = '23514';
              END IF;
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE TRIGGER trg_core_asset_metadata_owner_scope_guard
            BEFORE INSERT OR UPDATE ON core_asset_metadata
            FOR EACH ROW EXECUTE FUNCTION core_asset_metadata_owner_scope_guard()
            """
        )
    )

    op.execute(sa.schema.CreateSchema("story"))
    op.create_table(
        "storyrun_upload_sessions",
        sa.Column("upload_session_id", sa.String(36), primary_key=True),
        sa.Column("actor_scope_kind", sa.String(32), nullable=False),
        sa.Column("actor_scope_ref", sa.String(128), nullable=False),
        sa.Column("target_kind", sa.String(32), nullable=False),
        sa.Column("target_ref", sa.String(128), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("expected_media_type", sa.String(32), nullable=False),
        sa.Column("expected_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("expected_sha256", sa.String(64), nullable=False),
        sa.Column("part_size_bytes", sa.Integer(), nullable=False),
        sa.Column("max_total_bytes", sa.BigInteger(), nullable=False),
        sa.Column("max_parts", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("state_version", sa.BigInteger(), nullable=False),
        sa.Column("staging_key", sa.String(128), nullable=False),
        sa.Column("aggregate_sha256", sa.String(64)),
        sa.Column("actual_size_bytes", sa.BigInteger()),
        sa.Column("asset_ref", sa.String(256)),
        sa.Column("asset_version", sa.Integer()),
        sa.Column("derived_asset_ref", sa.String(256)),
        sa.Column("derived_asset_version", sa.Integer()),
        sa.Column("error_code", sa.String(64)),
        sa.Column(
            "admission_gate_open", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("claim_version", sa.BigInteger()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "actor_scope_kind IN ('PARENT_ACCOUNT','ORGANIZATION')",
            name="ck_core_upload_actor_kind",
        ),
        sa.CheckConstraint("length(actor_scope_ref) > 0", name="ck_core_upload_actor_ref"),
        sa.CheckConstraint(
            "target_kind = 'STORY_RUN' AND purpose = 'RUN_ARTWORK'", name="ck_core_upload_target"
        ),
        sa.CheckConstraint(
            "expected_media_type IN ('image/jpeg','image/png','image/webp')",
            name="ck_core_upload_media",
        ),
        sa.CheckConstraint(
            "expected_size_bytes BETWEEN 1 AND 20971520", name="ck_core_upload_expected_size"
        ),
        sa.CheckConstraint("length(expected_sha256) = 64", name="ck_core_upload_expected_sha"),
        sa.CheckConstraint(
            "part_size_bytes = 4194304 AND max_parts = 5 AND max_total_bytes = 20971520",
            name="ck_core_upload_limits",
        ),
        sa.CheckConstraint(
            "state IN ('RECEIVING','PENDING','PROCESSING','READY','FAILED','ABORTED','EXPIRED')",
            name="ck_core_upload_state",
        ),
        sa.CheckConstraint("state_version > 0", name="ck_core_upload_version"),
        sa.CheckConstraint(
            "asset_ref IS NULL OR asset_version > 0", name="ck_core_upload_asset_version"
        ),
        sa.CheckConstraint(
            "derived_asset_ref IS NULL OR derived_asset_version > 0",
            name="ck_core_upload_derived_version",
        ),
    )
    op.create_index(
        "ix_storyrun_upload_owner_state",
        "storyrun_upload_sessions",
        ["actor_scope_kind", "actor_scope_ref", "state"],
    )
    op.create_index(
        "ix_storyrun_upload_recovery", "storyrun_upload_sessions", ["state", "updated_at"]
    )

    op.create_table(
        "storyrun_upload_parts",
        sa.Column("upload_part_id", sa.String(36), primary_key=True),
        sa.Column("upload_session_id", sa.String(36), nullable=False),
        sa.Column("part_number", sa.Integer(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("storage_object_ref", sa.String(128), nullable=False),
        sa.Column(
            "received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["upload_session_id"],
            ["storyrun_upload_sessions.upload_session_id"],
            ondelete="CASCADE",
            name="fk_core_upload_part_session",
        ),
        sa.UniqueConstraint("upload_session_id", "part_number", name="uq_core_upload_part_number"),
        sa.CheckConstraint("part_number BETWEEN 1 AND 5", name="ck_core_upload_part_number"),
        sa.CheckConstraint("byte_size BETWEEN 1 AND 4194304", name="ck_core_upload_part_size"),
        sa.CheckConstraint("length(sha256) = 64", name="ck_core_upload_part_sha"),
    )

    op.create_table(
        "core_upload_command_receipts",
        sa.Column("receipt_id", sa.String(36), primary_key=True),
        sa.Column("actor_scope_kind", sa.String(32), nullable=False),
        sa.Column("actor_scope_ref", sa.String(128), nullable=False),
        sa.Column("operation", sa.String(32), nullable=False),
        sa.Column("idempotency_scope_kind", sa.String(32), nullable=False),
        sa.Column("idempotency_scope_ref", sa.String(128), nullable=False),
        sa.Column("idempotency_key_sha256", sa.String(64), nullable=False),
        sa.Column("request_fingerprint_sha256", sa.String(64), nullable=False),
        sa.Column("state", sa.String(12), nullable=False),
        sa.Column("response_status", sa.Integer()),
        sa.Column("response_resource_version", sa.BigInteger()),
        sa.Column("response_body", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("resource_ref", sa.String(36)),
        sa.Column("resource_version", sa.BigInteger()),
        sa.Column("state_version", sa.BigInteger(), server_default="1", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("finalized_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["resource_ref"],
            ["storyrun_upload_sessions.upload_session_id"],
            ondelete="RESTRICT",
            name="fk_core_upload_receipt_session",
        ),
        sa.UniqueConstraint(
            "actor_scope_kind",
            "actor_scope_ref",
            "operation",
            "idempotency_scope_kind",
            "idempotency_scope_ref",
            "idempotency_key_sha256",
            name="uq_core_upload_receipt_identity",
        ),
        sa.CheckConstraint(
            "actor_scope_kind IN ('PARENT_ACCOUNT','ORGANIZATION')",
            name="ck_core_upload_receipt_actor_kind",
        ),
        sa.CheckConstraint(
            "operation IN ('CREATE_UPLOAD_SESSION','COMPLETE_UPLOAD','ABORT_UPLOAD')",
            name="ck_core_upload_receipt_operation",
        ),
        sa.CheckConstraint(
            "idempotency_scope_kind IN ('COLLECTION','UPLOAD_SESSION')",
            name="ck_core_upload_receipt_scope_kind",
        ),
        sa.CheckConstraint(
            "length(idempotency_key_sha256) = 64 AND length(request_fingerprint_sha256) = 64",
            name="ck_core_upload_receipt_hashes",
        ),
        sa.CheckConstraint(
            "state IN ('PENDING','FINAL') AND state_version > 0",
            name="ck_core_upload_receipt_state",
        ),
        sa.CheckConstraint(
            "response_body IS NULL OR octet_length(response_body::text) <= 262144",
            name="ck_core_upload_receipt_body_bound",
        ),
        sa.CheckConstraint(
            "(state = 'PENDING' AND response_status IS NULL AND "
            "response_resource_version IS NULL AND response_body IS NULL "
            "AND finalized_at IS NULL) OR "
            "(state = 'FINAL' AND response_status BETWEEN 100 AND 599 "
            "AND response_body IS NOT NULL AND finalized_at IS NOT NULL)",
            name="ck_core_upload_receipt_final_shape",
        ),
    )
    op.create_index(
        "ix_core_upload_receipt_recovery", "core_upload_command_receipts", ["state", "created_at"]
    )

    op.create_table(
        "core_asset_lineage",
        sa.Column("lineage_id", sa.String(36), primary_key=True),
        sa.Column("source_asset_ref", sa.String(256), nullable=False),
        sa.Column("source_asset_version", sa.Integer(), nullable=False),
        sa.Column("derived_asset_ref", sa.String(256), nullable=False),
        sa.Column("derived_asset_version", sa.Integer(), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("derived_sha256", sa.String(64), nullable=False),
        sa.Column("source_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("derived_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("transform_kind", sa.String(48), nullable=False),
        sa.Column("transform_version", sa.String(48), nullable=False),
        sa.Column("scanner_name", sa.String(64), nullable=False),
        sa.Column("scanner_version", sa.String(128), nullable=False),
        sa.Column("scanner_sha256", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["source_asset_ref", "source_asset_version"],
            ["core_asset_metadata.asset_ref", "core_asset_metadata.asset_version"],
            ondelete="RESTRICT",
            name="fk_core_asset_lineage_source",
        ),
        sa.ForeignKeyConstraint(
            ["derived_asset_ref", "derived_asset_version"],
            ["core_asset_metadata.asset_ref", "core_asset_metadata.asset_version"],
            ondelete="RESTRICT",
            name="fk_core_asset_lineage_derived",
        ),
        sa.UniqueConstraint(
            "source_asset_ref",
            "source_asset_version",
            "derived_asset_ref",
            "derived_asset_version",
            "transform_kind",
            name="uq_core_asset_lineage_edge",
        ),
        sa.CheckConstraint(
            "source_asset_version > 0 AND derived_asset_version > 0",
            name="ck_core_asset_lineage_versions",
        ),
        sa.CheckConstraint(
            "length(source_sha256) = 64 AND length(derived_sha256) = 64 "
            "AND length(scanner_sha256) = 64",
            name="ck_core_asset_lineage_hashes",
        ),
        sa.CheckConstraint(
            "source_size_bytes BETWEEN 1 AND 20971520 AND derived_size_bytes BETWEEN 1 AND 5000000",
            name="ck_core_asset_lineage_sizes",
        ),
    )

    op.create_table(
        "runs",
        sa.Column("run_id", sa.String(36), primary_key=True),
        sa.Column("actor_scope_kind", sa.String(32), nullable=False),
        sa.Column("actor_scope_ref", sa.String(128), nullable=False),
        sa.Column("profile_ref", sa.String(128), nullable=False),
        sa.Column("run_state", sa.String(32), nullable=False),
        sa.Column("revision", sa.BigInteger(), nullable=False),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.Column("job_state", sa.String(32)),
        sa.Column("retryable", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("action_required", sa.String(32)),
        sa.Column("asset_ref", sa.String(256)),
        sa.Column("derived_asset_ref", sa.String(256)),
        sa.Column("understanding_revision", sa.Integer()),
        sa.Column("subject_label", sa.String(256)),
        sa.Column("confidence", sa.Numeric(4, 3)),
        sa.Column("result_sha256", sa.String(64)),
        sa.Column("raw_body_sha256", sa.String(64)),
        sa.Column("provider_job_id", sa.String(36)),
        sa.Column("provider_attempt_id", sa.String(36)),
        sa.Column(
            "dispatch_gate_open", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("dispatch_claimed_version", sa.BigInteger()),
        sa.Column("error_code", sa.String(64)),
        sa.Column("active_owner_parent_account_id", sa.String(128)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "run_id", "actor_scope_kind", "actor_scope_ref", name="uq_story_run_owner_scope"
        ),
        sa.CheckConstraint(
            "actor_scope_kind IN ('PARENT_ACCOUNT','ORGANIZATION')", name="ck_story_run_owner_kind"
        ),
        sa.CheckConstraint(
            "length(actor_scope_ref) > 0 AND length(profile_ref) > 0",
            name="ck_story_run_actor_refs",
        ),
        sa.CheckConstraint("revision > 0 AND version > 0", name="ck_story_run_versions"),
        sa.CheckConstraint(
            "run_state IN ('INPUT_PROCESSING','SUBJECT_REVIEW',"
            "'PREPARATION_REVIEW','DELETE_PENDING','FAILED')",
            name="ck_story_run_state",
        ),
        sa.CheckConstraint(
            "job_state IS NULL OR job_state IN ('QUEUED','RUNNING','SUCCEEDED',"
            "'FAILED','AWAITING_RECONCILIATION')",
            name="ck_story_run_job_state",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1", name="ck_story_run_confidence"
        ),
        schema="story",
    )
    op.create_index(
        "uq_story_run_active_parent",
        "runs",
        ["active_owner_parent_account_id"],
        unique=True,
        schema="story",
        postgresql_where=sa.text("active_owner_parent_account_id IS NOT NULL"),
    )
    op.create_index(
        "ix_story_run_owner_updated",
        "runs",
        ["actor_scope_kind", "actor_scope_ref", "updated_at"],
        schema="story",
    )

    op.create_table(
        "run_inputs",
        sa.Column("run_input_id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("input_revision", sa.Integer(), nullable=False),
        sa.Column("original_asset_ref", sa.String(256), nullable=False),
        sa.Column("original_asset_version", sa.Integer(), nullable=False),
        sa.Column("original_sha256", sa.String(64), nullable=False),
        sa.Column("original_media_type", sa.String(32), nullable=False),
        sa.Column("original_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("derived_asset_ref", sa.String(256), nullable=False),
        sa.Column("derived_asset_version", sa.Integer(), nullable=False),
        sa.Column("derived_sha256", sa.String(64), nullable=False),
        sa.Column("derived_media_type", sa.String(32), nullable=False),
        sa.Column("derived_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["story.runs.run_id"], ondelete="CASCADE", name="fk_story_run_input_run"
        ),
        sa.UniqueConstraint("run_id", "input_revision", name="uq_story_run_input_revision"),
        sa.UniqueConstraint("run_id", "run_input_id", name="uq_story_run_input_owner"),
        sa.CheckConstraint(
            "input_revision > 0 AND original_asset_version > 0 AND derived_asset_version > 0",
            name="ck_story_run_input_versions",
        ),
        sa.CheckConstraint(
            "length(original_sha256) = 64 AND length(derived_sha256) = 64",
            name="ck_story_run_input_hashes",
        ),
        sa.CheckConstraint(
            "original_size_bytes BETWEEN 1 AND 20971520 "
            "AND derived_size_bytes BETWEEN 1 AND 5000000",
            name="ck_story_run_input_sizes",
        ),
        schema="story",
    )

    op.create_table(
        "understanding_revisions",
        sa.Column("understanding_revision_id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("run_input_id", sa.String(36), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("subject_label", sa.String(256), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("canonical_result_sha256", sa.String(64), nullable=False),
        sa.Column("raw_body_sha256", sa.String(64)),
        sa.Column("result_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["run_id", "run_input_id"],
            ["story.run_inputs.run_id", "story.run_inputs.run_input_id"],
            ondelete="CASCADE",
            name="fk_story_understanding_run_input",
        ),
        sa.UniqueConstraint("run_id", "revision_no", name="uq_story_understanding_revision"),
        sa.CheckConstraint(
            "revision_no > 0 AND confidence BETWEEN 0 AND 1", name="ck_story_understanding_values"
        ),
        sa.CheckConstraint(
            "length(canonical_result_sha256) = 64 AND "
            "(raw_body_sha256 IS NULL OR length(raw_body_sha256) = 64)",
            name="ck_story_understanding_hashes",
        ),
        sa.CheckConstraint(
            "octet_length(result_snapshot::text) <= 262144",
            name="ck_story_understanding_snapshot_bound",
        ),
        schema="story",
    )

    op.create_table(
        "command_receipts",
        sa.Column("receipt_id", sa.String(36), primary_key=True),
        sa.Column("actor_scope_kind", sa.String(32), nullable=False),
        sa.Column("actor_scope_ref", sa.String(128), nullable=False),
        sa.Column("operation", sa.String(32), nullable=False),
        sa.Column("idempotency_scope_kind", sa.String(32), nullable=False),
        sa.Column("idempotency_scope_ref", sa.String(128), nullable=False),
        sa.Column("idempotency_key_sha256", sa.String(64), nullable=False),
        sa.Column("request_fingerprint_sha256", sa.String(64), nullable=False),
        sa.Column("state", sa.String(12), nullable=False),
        sa.Column("response_status", sa.Integer()),
        sa.Column("response_resource_version", sa.BigInteger()),
        sa.Column("response_body", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("resource_ref", sa.String(36)),
        sa.Column("resource_version", sa.BigInteger()),
        sa.Column("state_version", sa.BigInteger(), server_default="1", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("finalized_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["resource_ref"],
            ["story.runs.run_id"],
            ondelete="RESTRICT",
            name="fk_story_receipt_run",
        ),
        sa.UniqueConstraint(
            "actor_scope_kind",
            "actor_scope_ref",
            "operation",
            "idempotency_scope_kind",
            "idempotency_scope_ref",
            "idempotency_key_sha256",
            name="uq_story_command_receipt_identity",
        ),
        sa.CheckConstraint(
            "actor_scope_kind IN ('PARENT_ACCOUNT','ORGANIZATION')",
            name="ck_story_receipt_actor_kind",
        ),
        sa.CheckConstraint(
            "operation IN ('CREATE_RUN','ATTACH_ASSET','CONFIRM_SUBJECT','CANCEL_RUN')",
            name="ck_story_receipt_operation",
        ),
        sa.CheckConstraint(
            "idempotency_scope_kind IN ('COLLECTION','STORY_RUN')",
            name="ck_story_receipt_scope_kind",
        ),
        sa.CheckConstraint(
            "length(idempotency_key_sha256) = 64 AND length(request_fingerprint_sha256) = 64",
            name="ck_story_receipt_hashes",
        ),
        sa.CheckConstraint(
            "state IN ('PENDING','FINAL') AND state_version > 0", name="ck_story_receipt_state"
        ),
        sa.CheckConstraint(
            "response_body IS NULL OR octet_length(response_body::text) <= 262144",
            name="ck_story_receipt_body_bound",
        ),
        sa.CheckConstraint(
            "(state = 'PENDING' AND response_status IS NULL AND "
            "response_resource_version IS NULL AND response_body IS NULL "
            "AND finalized_at IS NULL) OR "
            "(state = 'FINAL' AND response_status BETWEEN 100 AND 599 "
            "AND response_body IS NOT NULL AND finalized_at IS NOT NULL)",
            name="ck_story_receipt_final_shape",
        ),
        schema="story",
    )
    op.create_index(
        "ix_story_receipt_recovery", "command_receipts", ["state", "created_at"], schema="story"
    )

    op.create_table(
        "review_decisions",
        sa.Column("decision_id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("command_receipt_id", sa.String(36), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("decision", sa.String(24), nullable=False),
        sa.Column("actor_scope_kind", sa.String(32), nullable=False),
        sa.Column("actor_scope_ref", sa.String(128), nullable=False),
        sa.Column("target_understanding_revision", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["story.runs.run_id"], ondelete="CASCADE", name="fk_story_review_run"
        ),
        sa.ForeignKeyConstraint(
            ["command_receipt_id"],
            ["story.command_receipts.receipt_id"],
            ondelete="RESTRICT",
            name="fk_story_review_receipt",
        ),
        sa.UniqueConstraint("command_receipt_id", name="uq_story_review_command_receipt"),
        sa.CheckConstraint(
            "stage = 'SUBJECT' AND decision = 'CONFIRM'", name="ck_story_review_decision_kind"
        ),
        sa.CheckConstraint(
            "target_understanding_revision > 0", name="ck_story_review_target_revision"
        ),
        schema="story",
    )


def downgrade() -> None:
    connection = op.get_bind()
    parent_rows = connection.execute(
        sa.text(
            "SELECT count(*) FROM core_asset_metadata WHERE owner_scope_kind = 'PARENT_ACCOUNT'"
        )
    ).scalar_one()
    if parent_rows:
        raise RuntimeError("cannot downgrade StoryRun-lite while typed Parent assets exist")
    op.drop_table("review_decisions", schema="story")
    op.drop_index("ix_story_receipt_recovery", table_name="command_receipts", schema="story")
    op.drop_table("command_receipts", schema="story")
    op.drop_table("understanding_revisions", schema="story")
    op.drop_table("run_inputs", schema="story")
    op.drop_index("ix_story_run_owner_updated", table_name="runs", schema="story")
    op.drop_index("uq_story_run_active_parent", table_name="runs", schema="story")
    op.drop_table("runs", schema="story")
    op.drop_table("core_asset_lineage")
    op.drop_index("ix_core_upload_receipt_recovery", table_name="core_upload_command_receipts")
    op.drop_table("core_upload_command_receipts")
    op.drop_table("storyrun_upload_parts")
    op.drop_index("ix_storyrun_upload_recovery", table_name="storyrun_upload_sessions")
    op.drop_index("ix_storyrun_upload_owner_state", table_name="storyrun_upload_sessions")
    op.drop_table("storyrun_upload_sessions")
    op.execute(sa.schema.DropSchema("story"))
    op.execute(
        sa.text("DROP TRIGGER trg_core_asset_metadata_owner_scope_guard ON core_asset_metadata")
    )
    op.execute(sa.text("DROP FUNCTION core_asset_metadata_owner_scope_guard()"))
    op.drop_index("ix_core_asset_typed_owner", table_name="core_asset_metadata")
    op.drop_constraint("ck_core_asset_owner_scope", "core_asset_metadata", type_="check")
    op.drop_column("core_asset_metadata", "owner_scope_ref")
    op.drop_column("core_asset_metadata", "owner_scope_kind")
    op.alter_column(
        "core_asset_metadata", "organization_id", existing_type=sa.String(128), nullable=False
    )
