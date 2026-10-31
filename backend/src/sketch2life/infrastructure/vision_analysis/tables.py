"""Independently migrated storage for the synthetic analysis-only pilot."""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

SCHEMA = "pilot_vision"
METADATA = MetaData(schema=SCHEMA)


def _org() -> Column[str]:
    return Column("organization_id", String(128), primary_key=True)


requests = Table(
    "request",
    METADATA,
    _org(),
    Column("assistance_id", String(256), primary_key=True),
    Column("record_version", Integer, nullable=False),
    Column("semantic_identity", String(128), nullable=False),
    Column("operation_target", String(512), nullable=False),
    Column("debounce_key", String(512), nullable=False),
    Column("session_id", String(256), nullable=False),
    Column("target_key", String(512), nullable=False),
    Column("status", String(32), nullable=False),
    Column("reservation", String(32)),
    Column("counts_for_debounce", Boolean, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSONB, nullable=False),
    CheckConstraint("record_version > 0", name="ck_pv_request_version"),
)
Index(
    "uq_pv_request_active_semantic",
    requests.c.organization_id,
    requests.c.semantic_identity,
    unique=True,
    postgresql_where=text("status IN ('scheduling', 'scheduled')"),
)

receipts = Table(
    "receipt",
    METADATA,
    _org(),
    Column("principal_id", String(256), primary_key=True),
    Column("contract_name", String(256), primary_key=True),
    Column("target_id", String(256), primary_key=True),
    Column("idempotency_key", String(256), primary_key=True),
    Column("assistance_id", String(256), nullable=False),
    Column("payload", JSONB, nullable=False),
    ForeignKeyConstraint(
        ["organization_id", "assistance_id"],
        [f"{SCHEMA}.request.organization_id", f"{SCHEMA}.request.assistance_id"],
        ondelete="CASCADE",
        name="fk_pv_receipt_request",
    ),
)
events = Table(
    "event",
    METADATA,
    _org(),
    Column("event_id", String(256), primary_key=True),
    Column("assistance_id", String(256)),
    Column("payload", JSONB, nullable=False),
    ForeignKeyConstraint(
        ["organization_id", "assistance_id"],
        [f"{SCHEMA}.request.organization_id", f"{SCHEMA}.request.assistance_id"],
        ondelete="CASCADE",
        name="fk_pv_event_request",
    ),
)
notices = Table("notice", METADATA, _org(), Column("notice_id", String(256), primary_key=True))
epochs = Table(
    "epoch",
    METADATA,
    _org(),
    Column("request_epoch", BigInteger, nullable=False, server_default="0"),
    Column("analysis_epoch", BigInteger, nullable=False, server_default="0"),
    CheckConstraint("request_epoch >= 0 AND analysis_epoch >= 0", name="ck_pv_epoch"),
)
analysis_heads = Table(
    "analysis_head",
    METADATA,
    _org(),
    Column("analysis_id", String(256), primary_key=True),
    Column("analysis_revision", Integer, nullable=False),
    Column("job_id", String(256), nullable=False),
    Column("attempt_id", String(256), nullable=False),
    Column("payload", JSONB, nullable=False),
    UniqueConstraint("job_id", "attempt_id", name="uq_pv_analysis_attempt"),
    CheckConstraint("analysis_revision > 0", name="ck_pv_analysis_revision"),
)


def _analysis_fk(name: str) -> ForeignKeyConstraint:
    return ForeignKeyConstraint(
        ["organization_id", "analysis_id"],
        [f"{SCHEMA}.analysis_head.organization_id", f"{SCHEMA}.analysis_head.analysis_id"],
        ondelete="CASCADE",
        name=name,
    )


observations = Table(
    "observation",
    METADATA,
    _org(),
    Column("analysis_id", String(256), primary_key=True),
    Column("payload", JSONB, nullable=False),
    _analysis_fk("fk_pv_observation_head"),
)
provider_results = Table(
    "provider_result",
    METADATA,
    _org(),
    Column("result_ref", String(256), primary_key=True),
    Column("analysis_id", String(256), nullable=False),
    Column("result_sha256", String(64), nullable=False),
    Column("payload", JSONB, nullable=False),
    _analysis_fk("fk_pv_provider_result_head"),
)
invocations = Table(
    "invocation",
    METADATA,
    Column("run_id", String(256), primary_key=True),
    Column("organization_id", String(128), nullable=False),
    Column("job_id", String(256), nullable=False),
    Column("attempt_id", String(256), nullable=False),
    Column("state", String(24), nullable=False),
    Column("claimed_at", DateTime(timezone=True), nullable=False),
    Column("sent_at", DateTime(timezone=True)),
    Column("finished_at", DateTime(timezone=True)),
    Column("result_sha256", String(64)),
    UniqueConstraint("job_id", "attempt_id", name="uq_pv_invocation_attempt"),
    CheckConstraint(
        "state IN ('CLAIMED','SENT','SUCCEEDED','FAILED','UNKNOWN')", name="ck_pv_invocation_state"
    ),
    CheckConstraint(
        "(state = 'CLAIMED' AND sent_at IS NULL AND finished_at IS NULL) OR "
        "(state = 'SENT' AND sent_at IS NOT NULL AND finished_at IS NULL) OR "
        "(state IN ('SUCCEEDED','FAILED','UNKNOWN') AND sent_at IS NOT NULL "
        "AND finished_at IS NOT NULL)",
        name="ck_pv_invocation_times",
    ),
)
