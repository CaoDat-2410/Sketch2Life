"""SQLAlchemy Core metadata for the AI-owned PostgreSQL schema ``ai_jobs`` (Phase B, B2).

Plan: FEAT-044 ``plan/PHASE_B_PLAN.md`` revision 3 §6; ADR-0018 D1/D2. BE2 owns only this
schema: no foreign key points into BE1 tables and owner references stay opaque strings.
The migration ``backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py`` is the frozen
DDL; integration tests compare it against this metadata.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

AI_JOBS_SCHEMA = "ai_jobs"

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

AI_JOBS_METADATA = MetaData(schema=AI_JOBS_SCHEMA, naming_convention=NAMING_CONVENTION)

JOB_STATES = (
    "queued",
    "running",
    "succeeded",
    "failed_retryable",
    "failed_exhausted",
    "blocked_unsafe",
    "cancelled",
)
RESULT_DISPOSITIONS = ("accepted", "stale", "rejected")
OUTBOX_KINDS = ("dispatch", "audit", "quarantine")
NOTICE_STATUSES = ("COMPLETE",)

_ID = 128
_CODE = 80
_SHA256_HEX = "'^[0-9a-f]{64}$'"


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(value) for value in values)})"


def _sha256(column: str) -> str:
    return f"{column} ~ {_SHA256_HEX}"


def _ts(name: str, *, nullable: bool) -> Column[datetime]:
    return Column(name, DateTime(timezone=True), nullable=nullable)


job = Table(
    "job",
    AI_JOBS_METADATA,
    Column("job_id", String(_ID), nullable=False),
    Column("organization_id", String(_ID), nullable=False),
    Column("job_type", String(_ID), nullable=False),
    Column("job_revision", BigInteger, nullable=False),
    Column("state", String(32), nullable=False),
    Column("session_id", String(_ID), nullable=True),
    Column("subject_refs", JSONB, nullable=False),
    Column("purpose_code", String(_ID), nullable=False),
    Column("target_id", String(_ID), nullable=False),
    Column("request_ref", JSONB, nullable=False),
    Column("correlation_id", String(_ID), nullable=False),
    Column("policy_snapshot_id", String(_ID), nullable=False),
    Column("policy_snapshot", JSONB, nullable=False),
    Column("progress", JSONB, nullable=False),
    Column("result_disposition", String(16), nullable=True),
    Column("result_refs", JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    Column("failure", JSONB, nullable=True),
    _ts("retry_not_before", nullable=True),
    _ts("completed_at", nullable=True),
    _ts("created_at", nullable=False),
    _ts("updated_at", nullable=False),
    Column("lineage_note", Text, nullable=True),
    Column("history", JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    Column("accepted_fences", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    PrimaryKeyConstraint("job_id"),
    CheckConstraint("job_revision >= 1", name="revision_positive"),
    CheckConstraint(_in("state", JOB_STATES), name="state_data25"),
    CheckConstraint(
        f"result_disposition IS NULL OR {_in('result_disposition', RESULT_DISPOSITIONS)}",
        name="result_disposition",
    ),
    CheckConstraint("jsonb_typeof(subject_refs) = 'array'", name="subject_refs_array"),
    CheckConstraint("jsonb_typeof(request_ref) = 'object'", name="request_ref_object"),
    CheckConstraint("jsonb_typeof(policy_snapshot) = 'object'", name="policy_snapshot_object"),
    CheckConstraint("jsonb_typeof(progress) = 'object'", name="progress_object"),
    CheckConstraint("jsonb_typeof(result_refs) = 'array'", name="result_refs_array"),
    CheckConstraint("failure IS NULL OR jsonb_typeof(failure) = 'object'", name="failure_object"),
    CheckConstraint("jsonb_typeof(history) = 'array'", name="history_array"),
    CheckConstraint("jsonb_typeof(accepted_fences) = 'object'", name="accepted_fences_object"),
)
# Owner notices match non-terminal jobs by organization (Δ10); retries are swept by due time (Δ11).
Index(None, job.c.organization_id, job.c.state)
Index(
    "ix_job_due_retry",
    job.c.retry_not_before,
    postgresql_where=text("state = 'failed_retryable'"),
)

attempt = Table(
    "attempt",
    AI_JOBS_METADATA,
    Column("attempt_id", String(_ID), nullable=False),
    Column(
        "job_id", String(_ID), ForeignKey("ai_jobs.job.job_id", ondelete="RESTRICT"), nullable=False
    ),
    Column("attempt_number", Integer, nullable=False),
    Column("request_ref", JSONB, nullable=False),
    _ts("created_at", nullable=False),
    _ts("dispatched_at", nullable=True),
    Column("dispatch_count", Integer, nullable=False, server_default=text("0")),
    _ts("started_at", nullable=True),
    _ts("finished_at", nullable=True),
    Column("outcome", String(40), nullable=True),
    PrimaryKeyConstraint("attempt_id"),
    UniqueConstraint("job_id", "attempt_number"),
    CheckConstraint("attempt_number >= 1", name="number_positive"),
    CheckConstraint("dispatch_count >= 0", name="dispatch_count_nonnegative"),
    CheckConstraint("jsonb_typeof(request_ref) = 'object'", name="request_ref_object"),
)
# Reconciler sweeps (Δ7/Δ11): dispatched-not-started and overdue running attempts.
Index(
    "ix_attempt_dispatched_not_started",
    attempt.c.dispatched_at,
    postgresql_where=text(
        "started_at IS NULL AND finished_at IS NULL AND dispatched_at IS NOT NULL"
    ),
)
Index(
    "ix_attempt_running",
    attempt.c.started_at,
    postgresql_where=text("started_at IS NOT NULL AND finished_at IS NULL"),
)

command_receipt = Table(
    "command_receipt",
    AI_JOBS_METADATA,
    Column("organization_id", String(_ID), nullable=False),
    Column("principal_id", String(_ID), nullable=False),
    Column("contract_name", String(_CODE), nullable=False),
    Column("target_id", String(_ID), nullable=False),
    Column("idempotency_key", String(_ID), nullable=False),
    Column("fingerprint", String(64), nullable=False),
    Column(
        "job_id", String(_ID), ForeignKey("ai_jobs.job.job_id", ondelete="RESTRICT"), nullable=False
    ),
    Column("outcome", String(40), nullable=False),
    Column("job_revision_at_commit", BigInteger, nullable=False),
    _ts("recorded_at", nullable=False),
    PrimaryKeyConstraint(
        "organization_id", "principal_id", "contract_name", "target_id", "idempotency_key"
    ),
    CheckConstraint(_sha256("fingerprint"), name="fingerprint_sha256"),
    CheckConstraint("job_revision_at_commit >= 1", name="revision_positive"),
)

# Semantic dedup identity (Δ4, rev2 PB-R02): the canonical sha256 is the only key. Raw columns are
# kept for audit; no unique index covers them, so a NULL session_id never weakens uniqueness.
semantic_request = Table(
    "semantic_request",
    AI_JOBS_METADATA,
    Column("semantic_key_sha256", String(64), nullable=False),
    Column("organization_id", String(_ID), nullable=False),
    Column("job_type", String(_ID), nullable=False),
    Column("request_id", String(_ID), nullable=False),
    Column("request_revision", Integer, nullable=False),
    Column("input_hash", String(64), nullable=False),
    Column("context_revision", Integer, nullable=False),
    Column("target_id", String(_ID), nullable=False),
    Column("purpose_code", String(_ID), nullable=False),
    Column("session_id", String(_ID), nullable=True),
    Column("subject_refs", JSONB, nullable=False),
    Column(
        "job_id", String(_ID), ForeignKey("ai_jobs.job.job_id", ondelete="RESTRICT"), nullable=False
    ),
    _ts("created_at", nullable=False),
    PrimaryKeyConstraint("semantic_key_sha256"),
    CheckConstraint(_sha256("semantic_key_sha256"), name="key_sha256"),
    CheckConstraint(_sha256("input_hash"), name="input_hash_sha256"),
    CheckConstraint("jsonb_typeof(subject_refs) = 'array'", name="subject_refs_array"),
)

# Authoritative completions only; non-authoritative guard verdicts are never stored here.
completion_receipt = Table(
    "completion_receipt",
    AI_JOBS_METADATA,
    Column("job_id", String(_ID), nullable=False),
    Column("attempt_id", String(_ID), nullable=False),
    Column("receipt_id", String(_ID), nullable=False),
    Column("fingerprint", String(64), nullable=False),
    Column("disposition", String(16), nullable=False),
    Column("reason_code", String(_CODE), nullable=True),
    Column("job_revision_after", BigInteger, nullable=False),
    _ts("recorded_at", nullable=False),
    PrimaryKeyConstraint("job_id", "attempt_id"),
    UniqueConstraint("receipt_id"),
    ForeignKeyConstraint(["job_id"], ["ai_jobs.job.job_id"], ondelete="RESTRICT"),
    ForeignKeyConstraint(["attempt_id"], ["ai_jobs.attempt.attempt_id"], ondelete="RESTRICT"),
    CheckConstraint(_sha256("fingerprint"), name="fingerprint_sha256"),
    CheckConstraint(_in("disposition", RESULT_DISPOSITIONS), name="disposition"),
    CheckConstraint("job_revision_after >= 1", name="revision_positive"),
)

cancellation_notice = Table(
    "cancellation_notice",
    AI_JOBS_METADATA,
    Column("notice_id", String(_ID), nullable=False),
    Column("organization_id", String(_ID), nullable=False),
    Column("reason_code", String(_CODE), nullable=False),
    Column("session_id", String(_ID), nullable=True),
    Column("job_type", String(_ID), nullable=True),
    Column("subject_ref", String(_ID), nullable=True),
    Column("status", String(16), nullable=False),
    Column("applied_count", Integer, nullable=False),
    _ts("recorded_at", nullable=False),
    PrimaryKeyConstraint("notice_id"),
    CheckConstraint(_in("status", NOTICE_STATUSES), name="status_complete"),
    CheckConstraint("applied_count >= 0", name="applied_count_nonnegative"),
)

# Transactional outbox (Δ6, Δ9, Δ14, Δ15). Payloads never carry worker capabilities or tokens.
outbox = Table(
    "outbox",
    AI_JOBS_METADATA,
    Column("message_id", String(_ID), nullable=False),
    Column("kind", String(16), nullable=False),
    Column("event_id", String(64), nullable=True),
    Column("organization_id", String(_ID), nullable=False),
    Column("job_id", String(_ID), nullable=True),
    Column("attempt_id", String(_ID), nullable=True),
    Column("payload", JSONB, nullable=False),
    _ts("available_at", nullable=False),
    _ts("delivered_at", nullable=True),
    Column("lease_owner", String(_ID), nullable=True),
    Column("lease_generation", BigInteger, nullable=False, server_default=text("0")),
    _ts("lease_until", nullable=True),
    Column("publish_attempts", Integer, nullable=False, server_default=text("0")),
    Column("last_error_code", String(_CODE), nullable=True),
    _ts("created_at", nullable=False),
    PrimaryKeyConstraint("message_id"),
    CheckConstraint(_in("kind", OUTBOX_KINDS), name="kind"),
    CheckConstraint(
        f"kind = 'dispatch' OR (event_id IS NOT NULL AND {_sha256('event_id')})",
        name="side_effect_event_id",
    ),
    CheckConstraint(
        "kind <> 'dispatch' OR (job_id IS NOT NULL AND attempt_id IS NOT NULL)",
        name="dispatch_identity",
    ),
    CheckConstraint("jsonb_typeof(payload) = 'object'", name="payload_object"),
    CheckConstraint(
        "NOT (payload ?| ARRAY['capability', 'token', 'worker_capability'])",
        name="payload_token_free",
    ),
    CheckConstraint("(lease_owner IS NULL) = (lease_until IS NULL)", name="lease_pair"),
    CheckConstraint("lease_generation >= 0", name="lease_generation_nonnegative"),
    CheckConstraint("publish_attempts >= 0", name="publish_attempts_nonnegative"),
)
Index(
    "uq_outbox_event_id",
    outbox.c.event_id,
    unique=True,
    postgresql_where=text("kind <> 'dispatch'"),
)
Index(
    "ix_outbox_pending",
    outbox.c.available_at,
    postgresql_where=text("delivered_at IS NULL"),
)

__all__ = [
    "AI_JOBS_METADATA",
    "AI_JOBS_SCHEMA",
    "JOB_STATES",
    "NOTICE_STATUSES",
    "OUTBOX_KINDS",
    "RESULT_DISPOSITIONS",
    "attempt",
    "cancellation_notice",
    "command_receipt",
    "completion_receipt",
    "job",
    "outbox",
    "semantic_request",
]
