"""Create the AI-owned ai_jobs schema for BE2-01 Phase B durable jobs.

Independent module branch ``ai_jobs`` beside ``be1_core`` (ADR-0018 D2, FEAT-044 Q1/Q7): no
foreign key into BE1 tables, so the branch has no BE1 dependency. Upgrade with
``upgrade ai_jobs@head`` (or ``upgrade heads`` for every module branch). Downgrade drops only
this schema and is for disposable test databases.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261015_ai_0001"
down_revision = None
branch_labels = ("ai_jobs",)
depends_on = None

SCHEMA = "ai_jobs"
_SHA = "~ '^[0-9a-f]{64}$'"


def _id(name: str, *, nullable: bool = False) -> sa.Column[str]:
    return sa.Column(name, sa.String(length=128), nullable=nullable)


def _code(name: str, *, nullable: bool = False) -> sa.Column[str]:
    return sa.Column(name, sa.String(length=80), nullable=nullable)


def _ts(name: str, *, nullable: bool) -> sa.Column[datetime]:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def _jsonb(name: str, *, default: str | None = None) -> sa.Column[Any]:
    server_default = sa.text(default) if default is not None else None
    return sa.Column(name, postgresql.JSONB(), nullable=False, server_default=server_default)


def upgrade() -> None:
    op.execute(sa.text(f"CREATE SCHEMA {SCHEMA}"))

    op.create_table(
        "job",
        _id("job_id"),
        _id("organization_id"),
        _id("job_type"),
        sa.Column("job_revision", sa.BigInteger(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        _id("session_id", nullable=True),
        _jsonb("subject_refs"),
        _id("purpose_code"),
        _id("target_id"),
        _jsonb("request_ref"),
        _id("correlation_id"),
        _id("policy_snapshot_id"),
        _jsonb("policy_snapshot"),
        _jsonb("progress"),
        sa.Column("result_disposition", sa.String(length=16), nullable=True),
        _jsonb("result_refs", default="'[]'::jsonb"),
        sa.Column("failure", postgresql.JSONB(), nullable=True),
        _ts("retry_not_before", nullable=True),
        _ts("completed_at", nullable=True),
        _ts("created_at", nullable=False),
        _ts("updated_at", nullable=False),
        sa.Column("lineage_note", sa.Text(), nullable=True),
        _jsonb("history", default="'[]'::jsonb"),
        _jsonb("accepted_fences", default="'{}'::jsonb"),
        sa.PrimaryKeyConstraint("job_id", name="pk_job"),
        sa.CheckConstraint("job_revision >= 1", name="ck_job_revision_positive"),
        sa.CheckConstraint(
            "state IN ('queued', 'running', 'succeeded', 'failed_retryable', "
            "'failed_exhausted', 'blocked_unsafe', 'cancelled')",
            name="ck_job_state_data25",
        ),
        sa.CheckConstraint(
            "result_disposition IS NULL OR result_disposition IN ('accepted', 'stale', 'rejected')",
            name="ck_job_result_disposition",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(subject_refs) = 'array'", name="ck_job_subject_refs_array"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(request_ref) = 'object'", name="ck_job_request_ref_object"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(policy_snapshot) = 'object'", name="ck_job_policy_snapshot_object"
        ),
        sa.CheckConstraint("jsonb_typeof(progress) = 'object'", name="ck_job_progress_object"),
        sa.CheckConstraint("jsonb_typeof(result_refs) = 'array'", name="ck_job_result_refs_array"),
        sa.CheckConstraint(
            "failure IS NULL OR jsonb_typeof(failure) = 'object'", name="ck_job_failure_object"
        ),
        sa.CheckConstraint("jsonb_typeof(history) = 'array'", name="ck_job_history_array"),
        sa.CheckConstraint(
            "jsonb_typeof(accepted_fences) = 'object'", name="ck_job_accepted_fences_object"
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_job_organization_id_state", "job", ["organization_id", "state"], schema=SCHEMA
    )
    op.create_index(
        "ix_job_due_retry",
        "job",
        ["retry_not_before"],
        schema=SCHEMA,
        postgresql_where=sa.text("state = 'failed_retryable'"),
    )

    op.create_table(
        "attempt",
        _id("attempt_id"),
        _id("job_id"),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        _jsonb("request_ref"),
        _ts("created_at", nullable=False),
        _ts("dispatched_at", nullable=True),
        sa.Column("dispatch_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        _ts("started_at", nullable=True),
        _ts("finished_at", nullable=True),
        sa.Column("outcome", sa.String(length=40), nullable=True),
        sa.PrimaryKeyConstraint("attempt_id", name="pk_attempt"),
        sa.UniqueConstraint("job_id", "attempt_number", name="uq_attempt_job_id_attempt_number"),
        sa.ForeignKeyConstraint(
            ["job_id"], [f"{SCHEMA}.job.job_id"], name="fk_attempt_job_id_job", ondelete="RESTRICT"
        ),
        sa.CheckConstraint("attempt_number >= 1", name="ck_attempt_number_positive"),
        sa.CheckConstraint("dispatch_count >= 0", name="ck_attempt_dispatch_count_nonnegative"),
        sa.CheckConstraint(
            "jsonb_typeof(request_ref) = 'object'", name="ck_attempt_request_ref_object"
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_attempt_dispatched_not_started",
        "attempt",
        ["dispatched_at"],
        schema=SCHEMA,
        postgresql_where=sa.text(
            "started_at IS NULL AND finished_at IS NULL AND dispatched_at IS NOT NULL"
        ),
    )
    op.create_index(
        "ix_attempt_running",
        "attempt",
        ["started_at"],
        schema=SCHEMA,
        postgresql_where=sa.text("started_at IS NOT NULL AND finished_at IS NULL"),
    )

    op.create_table(
        "command_receipt",
        _id("organization_id"),
        _id("principal_id"),
        _code("contract_name"),
        _id("target_id"),
        _id("idempotency_key"),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        _id("job_id"),
        sa.Column("outcome", sa.String(length=40), nullable=False),
        sa.Column("job_revision_at_commit", sa.BigInteger(), nullable=False),
        _ts("recorded_at", nullable=False),
        sa.PrimaryKeyConstraint(
            "organization_id",
            "principal_id",
            "contract_name",
            "target_id",
            "idempotency_key",
            name="pk_command_receipt",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            [f"{SCHEMA}.job.job_id"],
            name="fk_command_receipt_job_id_job",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(f"fingerprint {_SHA}", name="ck_command_receipt_fingerprint_sha256"),
        sa.CheckConstraint(
            "job_revision_at_commit >= 1", name="ck_command_receipt_revision_positive"
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "semantic_request",
        sa.Column("semantic_key_sha256", sa.String(length=64), nullable=False),
        _id("organization_id"),
        _id("job_type"),
        _id("request_id"),
        sa.Column("request_revision", sa.Integer(), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("context_revision", sa.Integer(), nullable=False),
        _id("target_id"),
        _id("purpose_code"),
        _id("session_id", nullable=True),
        _jsonb("subject_refs"),
        _id("job_id"),
        _ts("created_at", nullable=False),
        sa.PrimaryKeyConstraint("semantic_key_sha256", name="pk_semantic_request"),
        sa.ForeignKeyConstraint(
            ["job_id"],
            [f"{SCHEMA}.job.job_id"],
            name="fk_semantic_request_job_id_job",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(f"semantic_key_sha256 {_SHA}", name="ck_semantic_request_key_sha256"),
        sa.CheckConstraint(f"input_hash {_SHA}", name="ck_semantic_request_input_hash_sha256"),
        sa.CheckConstraint(
            "jsonb_typeof(subject_refs) = 'array'", name="ck_semantic_request_subject_refs_array"
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "completion_receipt",
        _id("job_id"),
        _id("attempt_id"),
        _id("receipt_id"),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("disposition", sa.String(length=16), nullable=False),
        _code("reason_code", nullable=True),
        sa.Column("job_revision_after", sa.BigInteger(), nullable=False),
        _ts("recorded_at", nullable=False),
        sa.PrimaryKeyConstraint("job_id", "attempt_id", name="pk_completion_receipt"),
        sa.UniqueConstraint("receipt_id", name="uq_completion_receipt_receipt_id"),
        sa.ForeignKeyConstraint(
            ["job_id"],
            [f"{SCHEMA}.job.job_id"],
            name="fk_completion_receipt_job_id_job",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            [f"{SCHEMA}.attempt.attempt_id"],
            name="fk_completion_receipt_attempt_id_attempt",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(f"fingerprint {_SHA}", name="ck_completion_receipt_fingerprint_sha256"),
        sa.CheckConstraint(
            "disposition IN ('accepted', 'stale', 'rejected')",
            name="ck_completion_receipt_disposition",
        ),
        sa.CheckConstraint(
            "job_revision_after >= 1", name="ck_completion_receipt_revision_positive"
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "cancellation_notice",
        _id("notice_id"),
        _id("organization_id"),
        _code("reason_code"),
        _id("session_id", nullable=True),
        _id("job_type", nullable=True),
        _id("subject_ref", nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("applied_count", sa.Integer(), nullable=False),
        _ts("recorded_at", nullable=False),
        sa.PrimaryKeyConstraint("notice_id", name="pk_cancellation_notice"),
        sa.CheckConstraint("status IN ('COMPLETE')", name="ck_cancellation_notice_status_complete"),
        sa.CheckConstraint(
            "applied_count >= 0", name="ck_cancellation_notice_applied_count_nonnegative"
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "outbox",
        _id("message_id"),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=True),
        _id("organization_id"),
        _id("job_id", nullable=True),
        _id("attempt_id", nullable=True),
        _jsonb("payload"),
        _ts("available_at", nullable=False),
        _ts("delivered_at", nullable=True),
        _id("lease_owner", nullable=True),
        sa.Column("lease_generation", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        _ts("lease_until", nullable=True),
        sa.Column("publish_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        _code("last_error_code", nullable=True),
        _ts("created_at", nullable=False),
        sa.PrimaryKeyConstraint("message_id", name="pk_outbox"),
        sa.CheckConstraint("kind IN ('dispatch', 'audit', 'quarantine')", name="ck_outbox_kind"),
        sa.CheckConstraint(
            f"kind = 'dispatch' OR (event_id IS NOT NULL AND event_id {_SHA})",
            name="ck_outbox_side_effect_event_id",
        ),
        sa.CheckConstraint(
            "kind <> 'dispatch' OR (job_id IS NOT NULL AND attempt_id IS NOT NULL)",
            name="ck_outbox_dispatch_identity",
        ),
        sa.CheckConstraint("jsonb_typeof(payload) = 'object'", name="ck_outbox_payload_object"),
        sa.CheckConstraint(
            "NOT (payload ?| ARRAY['capability', 'token', 'worker_capability'])",
            name="ck_outbox_payload_token_free",
        ),
        sa.CheckConstraint(
            "(lease_owner IS NULL) = (lease_until IS NULL)", name="ck_outbox_lease_pair"
        ),
        sa.CheckConstraint("lease_generation >= 0", name="ck_outbox_lease_generation_nonnegative"),
        sa.CheckConstraint("publish_attempts >= 0", name="ck_outbox_publish_attempts_nonnegative"),
        schema=SCHEMA,
    )
    op.create_index(
        "uq_outbox_event_id",
        "outbox",
        ["event_id"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("kind <> 'dispatch'"),
    )
    op.create_index(
        "ix_outbox_pending",
        "outbox",
        ["available_at"],
        schema=SCHEMA,
        postgresql_where=sa.text("delivered_at IS NULL"),
    )


def downgrade() -> None:
    for table in (
        "outbox",
        "cancellation_notice",
        "completion_receipt",
        "semantic_request",
        "command_receipt",
        "attempt",
        "job",
    ):
        op.drop_table(table, schema=SCHEMA)
    # RESTRICT: fails instead of removing anything this branch did not create.
    op.execute(sa.text(f"DROP SCHEMA {SCHEMA} RESTRICT"))
