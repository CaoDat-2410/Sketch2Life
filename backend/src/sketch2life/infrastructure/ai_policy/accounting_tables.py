"""Own resource ledger metadata; forward ap_0003, no foreign-owner relationships."""

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

from sketch2life.infrastructure.ai_policy.tables import SCHEMA

ACCOUNTING_METADATA = MetaData(schema=SCHEMA)
RESOURCE_SCOPE = Table(
    "resource_scope",
    ACCOUNTING_METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("feature_scope", String(120), primary_key=True),
    Column("occupied_slots", BigInteger, nullable=False),
    CheckConstraint("occupied_slots >= 0", name="resource_slots"),
)
BUCKET = Table(
    "budget_bucket",
    ACCOUNTING_METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("bucket_id", String(64), primary_key=True),
    Column("feature_scope", String(120), nullable=False),
    Column("key", JSONB, nullable=False),
    Column("held_units", BigInteger, nullable=False),
    Column("spent_units", BigInteger, nullable=False),
    ForeignKeyConstraint(
        ["organization_id", "feature_scope"],
        [f"{SCHEMA}.resource_scope.organization_id", f"{SCHEMA}.resource_scope.feature_scope"],
    ),
    UniqueConstraint("organization_id", "feature_scope", "bucket_id", name="budget_scope_key"),
    CheckConstraint("held_units >= 0 AND spent_units >= 0", name="budget_counters"),
)
RESERVATION = Table(
    "resource_reservation",
    ACCOUNTING_METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("reservation_id", String(120), primary_key=True),
    Column("feature_scope", String(120), nullable=False),
    Column("bucket_id", String(64), nullable=False),
    Column("request_digest", String(64), nullable=False),
    Column("attempt_id", String(120), nullable=False),
    Column("state", String(20), nullable=False),
    Column("payload", JSONB, nullable=False),
    ForeignKeyConstraint(
        ["organization_id", "feature_scope", "bucket_id"],
        [
            f"{SCHEMA}.budget_bucket.organization_id",
            f"{SCHEMA}.budget_bucket.feature_scope",
            f"{SCHEMA}.budget_bucket.bucket_id",
        ],
    ),
    UniqueConstraint(
        "organization_id", "feature_scope", "reservation_id", name="reservation_scope"
    ),
    UniqueConstraint("organization_id", "request_digest", "attempt_id", name="resource_attempt"),
    CheckConstraint("state IN ('reserved','consumed','released')", name="reservation_state"),
    CheckConstraint("request_digest ~ '^[0-9a-f]{64}$'", name="reservation_request_digest"),
)
LEDGER_RECEIPT = Table(
    "resource_receipt",
    ACCOUNTING_METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("principal_id", String(120), primary_key=True),
    Column("client_request_id", String(120), primary_key=True),
    Column("feature_scope", String(120), nullable=False),
    Column("fingerprint", String(64), nullable=False),
    Column("reservation_id", String(120), nullable=False),
    Column("operation", String(20), nullable=False),
    ForeignKeyConstraint(
        ["organization_id", "feature_scope", "reservation_id"],
        [
            f"{SCHEMA}.resource_reservation.organization_id",
            f"{SCHEMA}.resource_reservation.feature_scope",
            f"{SCHEMA}.resource_reservation.reservation_id",
        ],
    ),
    CheckConstraint(
        "operation IN ('reserve','consume','release','reconcile')", name="resource_operation"
    ),
    CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name="resource_fingerprint"),
)
LEDGER_EVENT = Table(
    "resource_event",
    ACCOUNTING_METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("event_id", String(120), primary_key=True),
    Column("feature_scope", String(120), nullable=False),
    Column("reservation_id", String(120), nullable=False),
    Column("principal_id", String(120), nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("delivered_at", DateTime(timezone=True)),
    ForeignKeyConstraint(
        ["organization_id", "feature_scope", "reservation_id"],
        [
            f"{SCHEMA}.resource_reservation.organization_id",
            f"{SCHEMA}.resource_reservation.feature_scope",
            f"{SCHEMA}.resource_reservation.reservation_id",
        ],
    ),
)
