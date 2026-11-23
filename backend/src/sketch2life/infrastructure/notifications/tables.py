"""Core table definition of DDL-C part 1 (migration ``20261120_nt_0001``), schema ``notifications``.

Columns, the dedupe constraint, the CHECK constraints and the two indexes: they must equal the
migration so that ``compare_metadata`` of the schema is empty (a unit test pins the CHECK texts to
the migration, the PostgreSQL test proves each of them). A separate ``MetaData`` keeps every other
module untouched. Only ``inbox_items`` exists here: the push endpoint and delivery attempt tables
are T-8b (deferred) and are deliberately not mirrored.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

SCHEMA = "notifications"
METADATA = sa.MetaData(schema=SCHEMA)

INBOX_ITEMS = sa.Table(
    "inbox_items",
    METADATA,
    sa.Column("inbox_item_id", sa.String(36), primary_key=True),
    sa.Column("recipient_account_id", sa.String(36), nullable=False),
    sa.Column("recipient_role", sa.String(24), nullable=False),
    sa.Column("organization_ref", sa.String(128)),
    sa.Column("notification_type", sa.String(64), nullable=False),
    sa.Column("template_version", sa.Integer(), nullable=False),
    sa.Column("trigger_id", sa.String(128), nullable=False),
    sa.Column("trigger_dedupe_key", sa.String(128), nullable=False),
    sa.Column("command_sha256", sa.String(64), nullable=False),
    sa.Column(
        "safe_parameters",
        JSONB,
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    ),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.Column("read_at", sa.DateTime(timezone=True)),
    sa.Column("expires_at", sa.DateTime(timezone=True)),
    sa.UniqueConstraint("recipient_account_id", "trigger_dedupe_key", name="uq_notif_inbox_dedupe"),
    sa.CheckConstraint(
        "recipient_role IN ('parent', 'teacher', 'school_manager', 'platform_admin')",
        name="ck_notif_inbox_role",
    ),
    sa.CheckConstraint("notification_type ~ '^[A-Z][A-Z0-9_]{2,63}$'", name="ck_notif_inbox_type"),
    sa.CheckConstraint("template_version BETWEEN 1 AND 9999", name="ck_notif_inbox_template"),
    sa.CheckConstraint(
        "trigger_id ~ '^[A-Za-z0-9._:-]{1,128}$' "
        "AND trigger_dedupe_key ~ '^[A-Za-z0-9._:-]{1,128}$'",
        name="ck_notif_inbox_keys",
    ),
    sa.CheckConstraint("command_sha256 ~ '^[0-9a-f]{64}$'", name="ck_notif_inbox_hash"),
    sa.CheckConstraint(
        "jsonb_typeof(safe_parameters) = 'object' AND octet_length(safe_parameters::text) <= 2048",
        name="ck_notif_inbox_params",
    ),
    sa.CheckConstraint(
        "(read_at IS NULL OR read_at >= created_at) "
        "AND (expires_at IS NULL OR expires_at > created_at)",
        name="ck_notif_inbox_times",
    ),
)

sa.Index(
    "ix_notif_inbox_page",
    INBOX_ITEMS.c.recipient_account_id,
    INBOX_ITEMS.c.created_at.desc(),
    INBOX_ITEMS.c.inbox_item_id.desc(),
)
sa.Index(
    "ix_notif_inbox_unread",
    INBOX_ITEMS.c.recipient_account_id,
    postgresql_where=sa.text("read_at IS NULL"),
)
