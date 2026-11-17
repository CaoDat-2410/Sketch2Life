"""Owned09 schema only; no FK/write into08, BE1 or foundation schemas."""

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

SCHEMA = "video_review"
METADATA = MetaData(schema=SCHEMA)


def _scope(*, video: bool = True) -> list[Column[str]]:
    names = (
        ("organization_id", "session_id", "video_id")
        if video
        else ("organization_id", "session_id")
    )
    return [Column(name, String(120), primary_key=True) for name in names]


HEAD = Table(
    "head",
    METADATA,
    *_scope(),
    Column("revision", BigInteger, nullable=False),
    Column("subject_digest", String(64), nullable=False),
    Column("payload", JSONB, nullable=False),
    CheckConstraint("revision > 0", name="head_revision"),
    CheckConstraint("subject_digest ~ '^[0-9a-f]{64}$'", name="head_digest"),
    CheckConstraint("jsonb_typeof(payload) = 'object'", name="head_object"),
)
RECEIPT = Table(
    "receipt",
    METADATA,
    *_scope(),
    Column("principal_id", String(120), primary_key=True),
    Column("client_key", String(120), primary_key=True),
    Column("kind", String(16), nullable=False),
    Column("revision", BigInteger, nullable=False),
    Column("payload", JSONB, nullable=False),
    CheckConstraint("kind IN ('write','change')", name="receipt_kind"),
    CheckConstraint("revision > 0", name="receipt_revision"),
    CheckConstraint("jsonb_typeof(payload) = 'object'", name="receipt_object"),
)
HISTORY = Table(
    "history",
    METADATA,
    *_scope(),
    Column("revision", BigInteger, primary_key=True),
    Column("payload", JSONB, nullable=False),
    CheckConstraint("revision > 0", name="history_revision"),
    CheckConstraint("jsonb_typeof(payload) = 'object'", name="history_object"),
)
PLAYBACK = Table(
    "playback",
    METADATA,
    *_scope(video=False),
    Column("principal_id", String(120), primary_key=True),
    Column("client_key", String(120), primary_key=True),
    Column("video_id", String(120), nullable=False),
    Column("revision", BigInteger, nullable=False),
    Column("state", String(16), nullable=False),
    Column("payload", JSONB, nullable=False),
    CheckConstraint("revision IN (1,2)", name="playback_revision"),
    CheckConstraint("state IN ('pending','playing','rejected')", name="playback_state"),
    CheckConstraint("jsonb_typeof(payload) = 'object'", name="playback_object"),
)
PLAYBACK_HISTORY = Table(
    "playback_history",
    METADATA,
    *_scope(video=False),
    Column("principal_id", String(120), primary_key=True),
    Column("client_key", String(120), primary_key=True),
    Column("revision", BigInteger, primary_key=True),
    Column("payload", JSONB, nullable=False),
    CheckConstraint("revision IN (1,2)", name="ph_revision"),
    CheckConstraint("jsonb_typeof(payload) = 'object'", name="ph_object"),
)
EVENT = Table(
    "event",
    METADATA,
    Column("organization_id", String(120), primary_key=True),
    Column("event_id", String(200), primary_key=True),
    Column("session_id", String(120), nullable=False),
    Column("video_id", String(120), nullable=False),
    Column("kind", String(40), nullable=False),
    Column("revision", BigInteger, nullable=False),
    Column("subject_digest", String(64), nullable=False),
    UniqueConstraint(
        "organization_id",
        "session_id",
        "video_id",
        "kind",
        "event_id",
        name="event_scoped_identity",
    ),
    CheckConstraint("revision > 0", name="event_revision"),
    CheckConstraint("subject_digest ~ '^[0-9a-f]{64}$'", name="event_digest"),
)
