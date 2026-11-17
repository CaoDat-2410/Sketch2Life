"""Owned08 metadata. No FK or write into foundation/BE1 schemas."""

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

SCHEMA = "knowledge_video"
METADATA = MetaData(schema=SCHEMA)

RUN = Table(
    "run", METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("video_id", String(120), primary_key=True),
    Column("session_id", String(120), nullable=False),
    Column("job_id", String(120), nullable=False),
    Column("run_revision", BigInteger, nullable=False),
    Column("pin_digest", String(64), nullable=False),
    Column("run_json", JSONB, nullable=False),
    UniqueConstraint("organization_id", "job_id", name="run_one_job"),
    UniqueConstraint("organization_id", "session_id", "pin_digest", name="run_one_semantic"),
    UniqueConstraint("organization_id", "session_id", "video_id", "pin_digest",
                     name="run_receipt_target"),
    CheckConstraint("run_revision > 0", name="run_revision_positive"),
    CheckConstraint("pin_digest ~ '^[0-9a-f]{64}$'", name="run_pin_hash"),
    CheckConstraint("jsonb_typeof(run_json) = 'object'", name="run_json_object"),
)

RECEIPT = Table(
    "receipt", METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("session_id", String(120), primary_key=True),
    Column("principal_id", String(120), primary_key=True),
    Column("idempotency_key", String(120), primary_key=True),
    Column("command_hash", String(64), nullable=False),
    Column("pin_digest", String(64), nullable=False),
    Column("video_id", String(120), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    ForeignKeyConstraint(
        ["organization_id", "session_id", "video_id", "pin_digest"],
        [f"{SCHEMA}.run.{column}" for column in (
            "organization_id", "session_id", "video_id", "pin_digest")],
        name="receipt_exact_run"
    ),
    CheckConstraint("command_hash ~ '^[0-9a-f]{64}$'", name="receipt_body_hash"),
    CheckConstraint("pin_digest ~ '^[0-9a-f]{64}$'", name="receipt_pin_hash"),
)
