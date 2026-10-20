"""Own scoped heads/history; all receipt/evaluation rows are immutable."""

from sqlalchemy import BigInteger, CheckConstraint, Column, MetaData, String, Table
from sqlalchemy.dialects.postgresql import JSONB

SCHEMA = "preset_automation"
METADATA = MetaData(schema=SCHEMA)
HEAD = Table(
    "head",
    METADATA,
    Column("organization_id", String(128), primary_key=True),
    Column("scope", String(128), primary_key=True),
    Column("object_key", String(128), primary_key=True),
    Column("revision", BigInteger, nullable=False),
    Column("payload", JSONB, nullable=False),
    CheckConstraint("revision >= 1", name="ck_pa_head_revision"),
)
HISTORY = Table(
    "history",
    METADATA,
    Column("organization_id", String(128), primary_key=True),
    Column("scope", String(128), primary_key=True),
    Column("object_key", String(128), primary_key=True),
    Column("revision", BigInteger, primary_key=True),
    Column("payload", JSONB, nullable=False),
    CheckConstraint("revision >= 1", name="ck_pa_history_revision"),
)
