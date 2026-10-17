"""Own durable original-copy inventory; no foreign-owner FKs or lifecycle duplication."""

from sqlalchemy import (
    BigInteger,
    Boolean,
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

COPY_METADATA = MetaData(schema=SCHEMA)
COPY_SCOPE = Table(
    "copy_scope",
    COPY_METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("scope_ref", String(120), primary_key=True),
    Column("revision", BigInteger, nullable=False),
    Column("purging", Boolean, nullable=False),
    CheckConstraint("revision >= 0", name="copy_scope_revision"),
)
COPY_REGISTRATION = Table(
    "copy_registration",
    COPY_METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("scope_ref", String(120), primary_key=True),
    Column("copy_id", String(120), primary_key=True),
    Column("kind", String(20), nullable=False),
    Column("original_profile_ref", JSONB, nullable=False),
    Column("initially_quarantined", Boolean, nullable=False),
    ForeignKeyConstraint(
        ["organization_id", "scope_ref"],
        [f"{SCHEMA}.copy_scope.organization_id", f"{SCHEMA}.copy_scope.scope_ref"],
    ),
    CheckConstraint("kind IN ('input','output','job','cache')", name="copy_registration_kind"),
)
COPY_COVERAGE = Table(
    "copy_coverage",
    COPY_METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("scope_ref", String(120), primary_key=True),
    Column("applied_revision", BigInteger, primary_key=True),
    Column("observation", JSONB, nullable=False),
    ForeignKeyConstraint(
        ["organization_id", "scope_ref"],
        [f"{SCHEMA}.copy_scope.organization_id", f"{SCHEMA}.copy_scope.scope_ref"],
    ),
    CheckConstraint("applied_revision > 0", name="copy_coverage_revision"),
)
COPY_EVENT = Table(
    "copy_registry_event",
    COPY_METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("event_id", String(120), primary_key=True),
    Column("scope_ref", String(120), nullable=False),
    Column("revision", BigInteger, nullable=False),
    Column("principal_id", String(120), nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("delivered_at", DateTime(timezone=True)),
    ForeignKeyConstraint(
        ["organization_id", "scope_ref"],
        [f"{SCHEMA}.copy_scope.organization_id", f"{SCHEMA}.copy_scope.scope_ref"],
    ),
    UniqueConstraint(
        "organization_id", "scope_ref", "revision", name="copy_registry_event_revision"
    ),
    CheckConstraint("revision > 0", name="copy_event_revision"),
)
