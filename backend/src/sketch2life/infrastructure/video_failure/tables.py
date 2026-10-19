"""Own10 tables; no cross-owner FK or direct writes."""

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

SCHEMA = "video_failure"
METADATA = MetaData(schema=SCHEMA)
INTENT = Table(
    "intent",
    METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("session_id", String(120), primary_key=True),
    Column("principal_id", String(120), primary_key=True),
    Column("client_key", String(120), primary_key=True),
    Column("disposition_id", String(120), nullable=False),
    Column("claim_key", String(64), nullable=False),
    Column("revision", BigInteger, nullable=False),
    Column("payload", JSONB, nullable=False),
    UniqueConstraint("organization_id", "claim_key", name="failure_one_winner"),
    UniqueConstraint("organization_id", "disposition_id", name="failure_disposition_id"),
    CheckConstraint("revision IN (1,2)", name="failure_revision"),
    CheckConstraint("claim_key ~ '^[0-9a-f]{64}$'", name="failure_claim"),
    CheckConstraint("jsonb_typeof(payload) = 'object'", name="failure_object"),
)
HISTORY = Table(
    "history",
    METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("disposition_id", String(120), primary_key=True),
    Column("revision", BigInteger, primary_key=True),
    Column("payload", JSONB, nullable=False),
    CheckConstraint("revision IN (1,2)", name="fh_revision"),
    CheckConstraint("jsonb_typeof(payload) = 'object'", name="fh_object"),
)
EVENT = Table(
    "event",
    METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("disposition_id", String(120), primary_key=True),
    Column("revision", BigInteger, primary_key=True),
    Column("operation_key", String(64), nullable=False),
    Column("target_digest", String(64), nullable=False),
    CheckConstraint("revision IN (1,2)", name="fe_revision"),
    CheckConstraint("operation_key ~ '^[0-9a-f]{64}$'", name="fe_operation"),
    CheckConstraint("target_digest ~ '^[0-9a-f]{64}$'", name="fe_target"),
)
