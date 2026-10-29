"""Own effective-scope/transition metadata added by forward migration ap_0002."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

from sketch2life.infrastructure.ai_policy.tables import SCHEMA

ACTIVATION_METADATA = MetaData(schema=SCHEMA)
SCOPE = Table(
    "effective_scope",
    ACTIVATION_METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("feature_scope", String(120), primary_key=True),
    Column("epoch", BigInteger, nullable=False),
    Column("record_id", String(120)),
    Column("version", Integer),
    Column("hash", String(64)),
    Column("disabled", Boolean, nullable=False),
    CheckConstraint("epoch >= 0", name="scope_epoch"),
    CheckConstraint(
        "(record_id IS NULL AND version IS NULL AND hash IS NULL) OR "
        "(record_id IS NOT NULL AND version IS NOT NULL AND hash IS NOT NULL "
        "AND version > 0 AND hash ~ '^[0-9a-f]{64}$')",
        name="scope_pin",
    ),
)
SCOPE_EVENT = Table(
    "scope_transition",
    ACTIVATION_METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("feature_scope", String(120), primary_key=True),
    Column("epoch", BigInteger, primary_key=True),
    Column("event_id", String(120), nullable=False),
    Column("principal_id", String(120), nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("delivered_at", DateTime(timezone=True)),
    ForeignKeyConstraint(
        ["organization_id", "feature_scope"],
        [f"{SCHEMA}.effective_scope.organization_id", f"{SCHEMA}.effective_scope.feature_scope"],
    ),
    UniqueConstraint("organization_id", "event_id", name="scope_event_unique"),
    CheckConstraint("epoch > 0", name="scope_event_epoch"),
)
