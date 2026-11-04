"""StoryRun-lite persistence metadata; no provider or framework behavior lives here."""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

CORE_METADATA = MetaData()
STORY_SCHEMA = "story"
STORY_METADATA = MetaData(schema=STORY_SCHEMA)

upload_sessions = Table(
    "storyrun_upload_sessions",
    CORE_METADATA,
    Column("upload_session_id", String(36), primary_key=True),
    Column("actor_scope_kind", String(32), nullable=False),
    Column("actor_scope_ref", String(128), nullable=False),
    Column("target_kind", String(32), nullable=False),
    Column("target_ref", String(128), nullable=False),
    Column("purpose", String(32), nullable=False),
    Column("expected_media_type", String(32), nullable=False),
    Column("expected_size_bytes", BigInteger, nullable=False),
    Column("expected_sha256", String(64), nullable=False),
    Column("part_size_bytes", Integer, nullable=False),
    Column("max_total_bytes", BigInteger, nullable=False),
    Column("max_parts", Integer, nullable=False),
    Column("state", String(24), nullable=False),
    Column("state_version", BigInteger, nullable=False),
    Column("staging_key", String(128), nullable=False),
    Column("aggregate_sha256", String(64)),
    Column("actual_size_bytes", BigInteger),
    Column("asset_ref", String(256)),
    Column("asset_version", Integer),
    Column("derived_asset_ref", String(256)),
    Column("derived_asset_version", Integer),
    Column("error_code", String(64)),
    Column("admission_gate_open", Boolean, nullable=False, server_default=text("false")),
    Column("claim_version", BigInteger),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    CheckConstraint(
        "expected_size_bytes BETWEEN 1 AND 20971520", name="ck_core_upload_expected_size"
    ),
    CheckConstraint("length(expected_sha256) = 64", name="ck_core_upload_expected_sha"),
    CheckConstraint(
        "part_size_bytes = 4194304 AND max_parts = 5 AND max_total_bytes = 20971520",
        name="ck_core_upload_limits",
    ),
    CheckConstraint(
        "state IN ('RECEIVING','PENDING','PROCESSING','READY','FAILED','ABORTED','EXPIRED')",
        name="ck_core_upload_state",
    ),
    CheckConstraint("state_version > 0", name="ck_core_upload_version"),
)
Index(
    "ix_storyrun_upload_owner_state",
    upload_sessions.c.actor_scope_kind,
    upload_sessions.c.actor_scope_ref,
    upload_sessions.c.state,
)
Index("ix_storyrun_upload_recovery", upload_sessions.c.state, upload_sessions.c.updated_at)

upload_parts = Table(
    "storyrun_upload_parts",
    CORE_METADATA,
    Column("upload_part_id", String(36), primary_key=True),
    Column(
        "upload_session_id",
        String(36),
        ForeignKey("storyrun_upload_sessions.upload_session_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("part_number", Integer, nullable=False),
    Column("byte_size", Integer, nullable=False),
    Column("sha256", String(64), nullable=False),
    Column("storage_object_ref", String(128), nullable=False),
    Column("received_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    UniqueConstraint("upload_session_id", "part_number", name="uq_core_upload_part_number"),
    CheckConstraint("part_number BETWEEN 1 AND 5", name="ck_core_upload_part_number"),
    CheckConstraint("byte_size BETWEEN 1 AND 4194304", name="ck_core_upload_part_size"),
    CheckConstraint("length(sha256) = 64", name="ck_core_upload_part_sha"),
)

upload_command_receipts = Table(
    "core_upload_command_receipts",
    CORE_METADATA,
    Column("receipt_id", String(36), primary_key=True),
    Column("actor_scope_kind", String(32), nullable=False),
    Column("actor_scope_ref", String(128), nullable=False),
    Column("operation", String(32), nullable=False),
    Column("idempotency_scope_kind", String(32), nullable=False),
    Column("idempotency_scope_ref", String(128), nullable=False),
    Column("idempotency_key_sha256", String(64), nullable=False),
    Column("request_fingerprint_sha256", String(64), nullable=False),
    Column("state", String(12), nullable=False),
    Column("response_status", Integer),
    Column("response_resource_version", BigInteger),
    Column("response_body", JSONB),
    Column(
        "resource_ref",
        String(36),
        ForeignKey("storyrun_upload_sessions.upload_session_id", ondelete="RESTRICT"),
    ),
    Column("resource_version", BigInteger),
    Column("state_version", BigInteger, nullable=False, server_default=text("1")),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("finalized_at", DateTime(timezone=True)),
    UniqueConstraint(
        "actor_scope_kind",
        "actor_scope_ref",
        "operation",
        "idempotency_scope_kind",
        "idempotency_scope_ref",
        "idempotency_key_sha256",
        name="uq_core_upload_receipt_identity",
    ),
    CheckConstraint(
        "actor_scope_kind IN ('PARENT_ACCOUNT','ORGANIZATION')",
        name="ck_core_upload_receipt_actor_kind",
    ),
    CheckConstraint(
        "operation IN ('CREATE_UPLOAD_SESSION','COMPLETE_UPLOAD','ABORT_UPLOAD')",
        name="ck_core_upload_receipt_operation",
    ),
    CheckConstraint(
        "idempotency_scope_kind IN ('COLLECTION','UPLOAD_SESSION')",
        name="ck_core_upload_receipt_scope_kind",
    ),
    CheckConstraint(
        "length(idempotency_key_sha256) = 64 AND length(request_fingerprint_sha256) = 64",
        name="ck_core_upload_receipt_hashes",
    ),
    CheckConstraint("state IN ('PENDING','FINAL')", name="ck_core_upload_receipt_state"),
    CheckConstraint("state_version > 0", name="ck_core_upload_receipt_version"),
    CheckConstraint(
        "response_body IS NULL OR octet_length(response_body::text) <= 262144",
        name="ck_core_upload_receipt_body_bound",
    ),
    CheckConstraint(
        "(state = 'PENDING' AND response_status IS NULL AND "
        "response_resource_version IS NULL AND response_body IS NULL "
        "AND finalized_at IS NULL) OR "
        "(state = 'FINAL' AND response_status BETWEEN 100 AND 599 "
        "AND response_body IS NOT NULL AND finalized_at IS NOT NULL)",
        name="ck_core_upload_receipt_final_shape",
    ),
)
Index(
    "ix_core_upload_receipt_recovery",
    upload_command_receipts.c.state,
    upload_command_receipts.c.created_at,
)

asset_lineage = Table(
    "core_asset_lineage",
    CORE_METADATA,
    Column("lineage_id", String(36), primary_key=True),
    Column("source_asset_ref", String(256), nullable=False),
    Column("source_asset_version", Integer, nullable=False),
    Column("derived_asset_ref", String(256), nullable=False),
    Column("derived_asset_version", Integer, nullable=False),
    Column("source_sha256", String(64), nullable=False),
    Column("derived_sha256", String(64), nullable=False),
    Column("source_size_bytes", BigInteger, nullable=False),
    Column("derived_size_bytes", BigInteger, nullable=False),
    Column("transform_kind", String(48), nullable=False),
    Column("transform_version", String(48), nullable=False),
    Column("scanner_name", String(64), nullable=False),
    Column("scanner_version", String(128), nullable=False),
    Column("scanner_sha256", String(64), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    UniqueConstraint(
        "source_asset_ref",
        "source_asset_version",
        "derived_asset_ref",
        "derived_asset_version",
        "transform_kind",
        name="uq_core_asset_lineage_edge",
    ),
    CheckConstraint(
        "source_asset_version > 0 AND derived_asset_version > 0",
        name="ck_core_asset_lineage_versions",
    ),
    CheckConstraint(
        "length(source_sha256) = 64 AND length(derived_sha256) = 64 "
        "AND length(scanner_sha256) = 64",
        name="ck_core_asset_lineage_hashes",
    ),
    CheckConstraint(
        "source_size_bytes > 0 AND derived_size_bytes > 0", name="ck_core_asset_lineage_sizes"
    ),
    # The migration adds the composite FKs to core_asset_metadata; it is mapped by the existing
    # Core metadata object, which is kept separate to preserve the approved file boundary.
)

story_runs = Table(
    "runs",
    STORY_METADATA,
    Column("run_id", String(36), primary_key=True),
    Column("actor_scope_kind", String(32), nullable=False),
    Column("actor_scope_ref", String(128), nullable=False),
    Column("profile_ref", String(128), nullable=False),
    Column("child_age_months", Integer, nullable=True),
    Column("run_state", String(32), nullable=False),
    Column("revision", BigInteger, nullable=False),
    Column("version", BigInteger, nullable=False),
    Column("job_state", String(32)),
    Column("retryable", Boolean, nullable=False, server_default=text("false")),
    Column("action_required", String(32)),
    Column("asset_ref", String(256)),
    Column("derived_asset_ref", String(256)),
    Column("understanding_revision", Integer),
    Column("subject_label", String(256)),
    Column("confidence", Numeric(4, 3)),
    Column("result_sha256", String(64)),
    Column("raw_body_sha256", String(64)),
    Column("provider_job_id", String(36)),
    Column("provider_attempt_id", String(36)),
    Column("dispatch_gate_open", Boolean, nullable=False, server_default=text("false")),
    Column("dispatch_claimed_version", BigInteger),
    Column("error_code", String(64)),
    Column("active_owner_parent_account_id", String(128)),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    UniqueConstraint(
        "run_id", "actor_scope_kind", "actor_scope_ref", name="uq_story_run_owner_scope"
    ),
    CheckConstraint(
        "actor_scope_kind IN ('PARENT_ACCOUNT','ORGANIZATION')", name="ck_story_run_owner_kind"
    ),
    CheckConstraint("revision > 0 AND version > 0", name="ck_story_run_versions"),
    CheckConstraint(
        "run_state IN ('INPUT_PROCESSING','SUBJECT_REVIEW',"
        "'PREPARATION_REVIEW','SCRIPT_GENERATING','SCRIPT_GENERATION_UNKNOWN','SCRIPT_REVIEW',"
        "'VIDEO_ADMISSION_PENDING','DELETE_PENDING','FAILED')",
        name="ck_story_run_state",
    ),
    CheckConstraint(
        "child_age_months IS NULL OR child_age_months BETWEEN 36 AND 120",
        name="ck_story_run_child_age_months",
    ),
    CheckConstraint(
        "job_state IS NULL OR job_state IN ('QUEUED','RUNNING','SUCCEEDED',"
        "'FAILED','AWAITING_RECONCILIATION')",
        name="ck_story_run_job_state",
    ),
    CheckConstraint(
        "confidence IS NULL OR confidence BETWEEN 0 AND 1", name="ck_story_run_confidence"
    ),
)
Index(
    "uq_story_run_active_parent",
    story_runs.c.active_owner_parent_account_id,
    unique=True,
    postgresql_where=story_runs.c.active_owner_parent_account_id.is_not(None),
)
Index(
    "ix_story_run_owner_updated",
    story_runs.c.actor_scope_kind,
    story_runs.c.actor_scope_ref,
    story_runs.c.updated_at,
)

run_inputs = Table(
    "run_inputs",
    STORY_METADATA,
    Column("run_input_id", String(36), primary_key=True),
    Column(
        "run_id", String(36), ForeignKey("story.runs.run_id", ondelete="CASCADE"), nullable=False
    ),
    Column("input_revision", Integer, nullable=False),
    Column("original_asset_ref", String(256), nullable=False),
    Column("original_asset_version", Integer, nullable=False),
    Column("original_sha256", String(64), nullable=False),
    Column("original_media_type", String(32), nullable=False),
    Column("original_size_bytes", BigInteger, nullable=False),
    Column("derived_asset_ref", String(256), nullable=False),
    Column("derived_asset_version", Integer, nullable=False),
    Column("derived_sha256", String(64), nullable=False),
    Column("derived_media_type", String(32), nullable=False),
    Column("derived_size_bytes", BigInteger, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    UniqueConstraint("run_id", "input_revision", name="uq_story_run_input_revision"),
    UniqueConstraint("run_id", "run_input_id", name="uq_story_run_input_owner"),
    CheckConstraint(
        "input_revision > 0 AND original_asset_version > 0 AND derived_asset_version > 0",
        name="ck_story_run_input_versions",
    ),
    CheckConstraint(
        "length(original_sha256) = 64 AND length(derived_sha256) = 64",
        name="ck_story_run_input_hashes",
    ),
    CheckConstraint(
        "original_size_bytes BETWEEN 1 AND 20971520 AND derived_size_bytes BETWEEN 1 AND 5000000",
        name="ck_story_run_input_sizes",
    ),
)

understanding_revisions = Table(
    "understanding_revisions",
    STORY_METADATA,
    Column("understanding_revision_id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("run_input_id", String(36), nullable=False),
    Column("revision_no", Integer, nullable=False),
    Column("subject_label", String(256), nullable=False),
    Column("confidence", Numeric(4, 3), nullable=False),
    Column("canonical_result_sha256", String(64), nullable=False),
    Column("raw_body_sha256", String(64)),
    Column("result_snapshot", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    ForeignKeyConstraint(
        ["run_id", "run_input_id"],
        ["story.run_inputs.run_id", "story.run_inputs.run_input_id"],
        ondelete="CASCADE",
        name="fk_story_understanding_run_input",
    ),
    UniqueConstraint("run_id", "revision_no", name="uq_story_understanding_revision"),
    CheckConstraint(
        "revision_no > 0 AND confidence BETWEEN 0 AND 1", name="ck_story_understanding_values"
    ),
    CheckConstraint(
        "length(canonical_result_sha256) = 64 AND "
        "(raw_body_sha256 IS NULL OR length(raw_body_sha256) = 64)",
        name="ck_story_understanding_hashes",
    ),
    CheckConstraint(
        "octet_length(result_snapshot::text) <= 262144",
        name="ck_story_understanding_snapshot_bound",
    ),
)

story_command_receipts = Table(
    "command_receipts",
    STORY_METADATA,
    Column("receipt_id", String(36), primary_key=True),
    Column("actor_scope_kind", String(32), nullable=False),
    Column("actor_scope_ref", String(128), nullable=False),
    Column("operation", String(32), nullable=False),
    Column("idempotency_scope_kind", String(32), nullable=False),
    Column("idempotency_scope_ref", String(128), nullable=False),
    Column("idempotency_key_sha256", String(64), nullable=False),
    Column("request_fingerprint_sha256", String(64), nullable=False),
    Column("state", String(12), nullable=False),
    Column("response_status", Integer),
    Column("response_resource_version", BigInteger),
    Column("response_body", JSONB),
    Column("resource_ref", String(36), ForeignKey("story.runs.run_id", ondelete="RESTRICT")),
    Column("resource_version", BigInteger),
    Column("state_version", BigInteger, nullable=False, server_default=text("1")),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("finalized_at", DateTime(timezone=True)),
    UniqueConstraint(
        "actor_scope_kind",
        "actor_scope_ref",
        "operation",
        "idempotency_scope_kind",
        "idempotency_scope_ref",
        "idempotency_key_sha256",
        name="uq_story_command_receipt_identity",
    ),
    CheckConstraint(
        "actor_scope_kind IN ('PARENT_ACCOUNT','ORGANIZATION')", name="ck_story_receipt_actor_kind"
    ),
    CheckConstraint(
        "operation IN ('CREATE_RUN','ATTACH_ASSET','CONFIRM_SUBJECT','CANCEL_RUN',"
        "'GENERATE_STORY_REVISION','CONFIRM_STORY_REVISION')",
        name="ck_story_receipt_operation",
    ),
    CheckConstraint(
        "idempotency_scope_kind IN ('COLLECTION','STORY_RUN')", name="ck_story_receipt_scope_kind"
    ),
    CheckConstraint(
        "length(idempotency_key_sha256) = 64 AND length(request_fingerprint_sha256) = 64",
        name="ck_story_receipt_hashes",
    ),
    CheckConstraint(
        "state IN ('PENDING','FINAL') AND state_version > 0", name="ck_story_receipt_state"
    ),
    CheckConstraint(
        "response_body IS NULL OR octet_length(response_body::text) <= 262144",
        name="ck_story_receipt_body_bound",
    ),
    CheckConstraint(
        "(state = 'PENDING' AND response_status IS NULL AND "
        "response_resource_version IS NULL AND response_body IS NULL "
        "AND finalized_at IS NULL) OR "
        "(state = 'FINAL' AND response_status BETWEEN 100 AND 599 "
        "AND response_body IS NOT NULL AND finalized_at IS NOT NULL)",
        name="ck_story_receipt_final_shape",
    ),
)
Index(
    "ix_story_receipt_recovery", story_command_receipts.c.state, story_command_receipts.c.created_at
)

review_decisions = Table(
    "review_decisions",
    STORY_METADATA,
    Column("decision_id", String(36), primary_key=True),
    Column(
        "run_id", String(36), ForeignKey("story.runs.run_id", ondelete="CASCADE"), nullable=False
    ),
    Column(
        "command_receipt_id",
        String(36),
        ForeignKey("story.command_receipts.receipt_id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    ),
    Column("stage", String(32), nullable=False),
    Column("decision", String(24), nullable=False),
    Column("actor_scope_kind", String(32), nullable=False),
    Column("actor_scope_ref", String(128), nullable=False),
    Column("target_understanding_revision", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    CheckConstraint(
        "stage = 'SUBJECT' AND decision = 'CONFIRM'", name="ck_story_review_decision_kind"
    ),
    CheckConstraint("target_understanding_revision > 0", name="ck_story_review_target_revision"),
)

story_revisions = Table(
    "story_revisions",
    STORY_METADATA,
    Column("story_revision_id", String(36), primary_key=True),
    Column(
        "run_id", String(36), ForeignKey("story.runs.run_id", ondelete="CASCADE"), nullable=False
    ),
    Column("revision_no", Integer, nullable=False),
    Column("status", String(32), nullable=False),
    Column("source_asset_sha256", String(64), nullable=False),
    Column("understanding_revision", Integer, nullable=False),
    Column("context_revision", Integer, nullable=False),
    Column("story_sha256", String(64)),
    Column("language", String(8)),
    Column("title", String(120)),
    Column("duration_ms", Integer),
    Column("story_content", JSONB),
    Column("schema_version", String(64), nullable=False),
    Column("prompt_version", String(64), nullable=False),
    Column("model_id", String(256), nullable=False),
    Column("model_revision", String(128), nullable=False),
    Column("request_sha256", String(64), nullable=False),
    Column("provider_call_id", String(128)),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    UniqueConstraint("run_id", "revision_no", name="uq_story_revision_run_no"),
    UniqueConstraint("run_id", "story_revision_id", name="uq_story_revision_run_owner"),
    CheckConstraint("revision_no BETWEEN 1 AND 4", name="ck_story_revision_no"),
    CheckConstraint(
        "status IN ('GENERATING','DRAFT','CONFIRMED','SUPERSEDED',"
        "'FAILED','AWAITING_RECONCILIATION')",
        name="ck_story_revision_status",
    ),
    CheckConstraint(
        "understanding_revision > 0 AND context_revision > 0", name="ck_story_revision_inputs"
    ),
    CheckConstraint(
        "length(source_asset_sha256) = 64 AND length(request_sha256) = 64",
        name="ck_story_revision_hashes",
    ),
    CheckConstraint(
        "story_sha256 IS NULL OR length(story_sha256) = 64", name="ck_story_revision_content_hash"
    ),
    CheckConstraint(
        "duration_ms IS NULL OR duration_ms BETWEEN 30000 AND 90000",
        name="ck_story_revision_duration",
    ),
    CheckConstraint(
        "(status IN ('GENERATING','FAILED','AWAITING_RECONCILIATION') AND story_sha256 IS NULL) OR "
        "(status IN ('DRAFT','CONFIRMED','SUPERSEDED') AND story_sha256 IS NOT NULL AND "
        "language = 'vi' AND title IS NOT NULL AND duration_ms IS NOT NULL "
        "AND story_content IS NOT NULL)",
        name="ck_story_revision_result_shape",
    ),
)
Index("ix_story_revision_run_status", story_revisions.c.run_id, story_revisions.c.status)

story_scenes = Table(
    "story_scenes",
    STORY_METADATA,
    Column("scene_id", String(36), primary_key=True),
    Column(
        "story_revision_id",
        String(36),
        ForeignKey("story.story_revisions.story_revision_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("scene_index", Integer, nullable=False),
    Column("title", String(100), nullable=False),
    Column("action", String(500), nullable=False),
    Column("visual_prompt", String(900), nullable=False),
    Column("narration", String(500), nullable=False),
    Column("start_ms", Integer, nullable=False),
    Column("duration_ms", Integer, nullable=False),
    Column("character_anchors", JSONB, nullable=False),
    UniqueConstraint("story_revision_id", "scene_index", name="uq_story_scene_revision_index"),
    CheckConstraint("scene_index BETWEEN 1 AND 15", name="ck_story_scene_index"),
    CheckConstraint(
        "start_ms >= 0 AND duration_ms BETWEEN 1000 AND 20000", name="ck_story_scene_timing"
    ),
)
Index("ix_story_scene_revision_order", story_scenes.c.story_revision_id, story_scenes.c.scene_index)

story_revision_reviews = Table(
    "story_revision_reviews",
    STORY_METADATA,
    Column("review_id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("story_revision_id", String(36), nullable=False),
    Column(
        "command_receipt_id",
        String(36),
        ForeignKey("story.command_receipts.receipt_id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    ),
    Column("actor_scope_kind", String(32), nullable=False),
    Column("actor_scope_ref", String(128), nullable=False),
    Column("decision", String(24), nullable=False),
    Column("target_story_sha256", String(64), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    ForeignKeyConstraint(
        ["run_id", "story_revision_id"],
        ["story.story_revisions.run_id", "story.story_revisions.story_revision_id"],
        ondelete="CASCADE",
        name="fk_story_revision_review_owner",
    ),
    UniqueConstraint("story_revision_id", name="uq_story_revision_review_once"),
    CheckConstraint("decision = 'CONFIRM'", name="ck_story_revision_review_decision"),
    CheckConstraint("length(target_story_sha256) = 64", name="ck_story_revision_review_hash"),
)


__all__ = [
    "CORE_METADATA",
    "STORY_METADATA",
    "STORY_SCHEMA",
    "asset_lineage",
    "review_decisions",
    "run_inputs",
    "story_command_receipts",
    "story_revisions",
    "story_scenes",
    "story_revision_reviews",
    "story_runs",
    "understanding_revisions",
    "upload_command_receipts",
    "upload_parts",
    "upload_sessions",
]
