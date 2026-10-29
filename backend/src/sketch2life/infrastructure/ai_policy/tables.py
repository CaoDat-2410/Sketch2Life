"""Owned lifecycle schema; activation/accounting added when implemented in C3."""

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

SCHEMA = "ai_policy"
METADATA = MetaData(schema=SCHEMA)


def scope_columns() -> list[Column[str]]:
    return [Column("organization_id", String(120), primary_key=True),
            Column("record_id", String(120), primary_key=True)]


RECORD = Table(
    "record", METADATA, *scope_columns(),
    Column("current_version", Integer, nullable=False),
    Column("revision", BigInteger, nullable=False),
    CheckConstraint("current_version > 0 AND revision > 0", name="record_positive"),
)
VERSION = Table(
    "version", METADATA, *scope_columns(),
    Column("version", Integer, primary_key=True),
    Column("body_json", Text, nullable=False),
    Column("hash", String(64), nullable=False),
    Column("state", String(24), nullable=False),
    Column("authored_by", String(120), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("context_revision", BigInteger, nullable=False),
    Column("review_revision", BigInteger, nullable=False),
    Column("publication_review_ids", JSONB, nullable=False),
    Column("publication_policy_version", String(120)),
    Column("recalled_at", DateTime(timezone=True)),
    Column("recall_reason", String(200)),
    ForeignKeyConstraint(["organization_id", "record_id"],
                         [f"{SCHEMA}.record.organization_id", f"{SCHEMA}.record.record_id"]),
    CheckConstraint("version > 0 AND context_revision >= 0 AND review_revision >= 0",
                    name="version_positive"),
    CheckConstraint("hash ~ '^[0-9a-f]{64}$'", name="version_hash"),
    CheckConstraint("state IN ('draft','submitted','changes_requested','published',"
                    "'recalled','archived')", name="version_state"),
)
REVIEW = Table(
    "review", METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("review_id", String(120), primary_key=True),
    Column("record_id", String(120), nullable=False),
    Column("version", Integer, nullable=False),
    Column("context_revision", BigInteger, nullable=False),
    Column("review_revision", BigInteger, nullable=False),
    Column("dimension", String(24), nullable=False),
    Column("proof", JSONB, nullable=False),
    ForeignKeyConstraint(["organization_id", "record_id", "version"],
                         [f"{SCHEMA}.version.organization_id", f"{SCHEMA}.version.record_id",
                          f"{SCHEMA}.version.version"]),
    UniqueConstraint("organization_id", "record_id", "version", "review_revision",
                     name="review_revision_unique"),
    CheckConstraint("dimension IN ('safety','pedagogical')", name="review_dimension"),
    CheckConstraint("context_revision > 0 AND review_revision > 0", name="review_positive"),
)
RECEIPT = Table(
    "receipt", METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("principal_id", String(120), primary_key=True),
    Column("request_id", String(120), primary_key=True),
    Column("fingerprint", String(64), nullable=False),
    Column("result_json", Text, nullable=False),
    CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name="receipt_hash"),
)
EVENT = Table(
    "event", METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("event_id", String(120), primary_key=True),
    Column("record_id", String(120), nullable=False),
    Column("version", Integer, nullable=False),
    Column("revision", BigInteger, nullable=False),
    Column("kind", String(80), nullable=False),
    Column("principal_id", String(120), nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSONB, nullable=False),
    ForeignKeyConstraint(["organization_id", "record_id", "version"],
                         [f"{SCHEMA}.version.organization_id", f"{SCHEMA}.version.record_id",
                          f"{SCHEMA}.version.version"]),
    UniqueConstraint("organization_id", "record_id", "revision", name="event_revision_unique"),
)
OUTBOX = Table(
    "outbox", METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("event_id", String(120), primary_key=True),
    Column("payload", JSONB, nullable=False),
    Column("delivered_at", DateTime(timezone=True)),
    ForeignKeyConstraint(["organization_id", "event_id"],
                         [f"{SCHEMA}.event.organization_id", f"{SCHEMA}.event.event_id"]),
)
