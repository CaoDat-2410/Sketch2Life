"""Core table definitions of DDL-C (migrations ``nt_0001`` through ``nt_0003``).

The columns, constraints and indexes mirror their migrations so metadata comparison is meaningful.
A separate ``MetaData`` keeps every other module untouched. Push delivery rows contain no payload,
endpoint ciphertext, fingerprint or provider response.
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

PUSH_ENDPOINTS = sa.Table(
    "push_endpoints",
    METADATA,
    sa.Column("push_endpoint_id", sa.String(36), primary_key=True),
    sa.Column("recipient_account_id", sa.String(36), nullable=False),
    sa.Column("platform_kind", sa.String(24), nullable=False),
    sa.Column("provider_kind", sa.String(24), nullable=False),
    sa.Column("endpoint_ciphertext", sa.LargeBinary, nullable=False),
    sa.Column("endpoint_fingerprint", sa.String(64), nullable=False),
    sa.Column("state", sa.String(16), server_default=sa.text("'ACTIVE'"), nullable=False),
    sa.Column("version", sa.Integer, server_default=sa.text("1"), nullable=False),
    sa.Column(
        "registered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.Column(
        "last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.Column("revoked_at", sa.DateTime(timezone=True)),
    sa.Column("app_version", sa.String(64)),
    sa.CheckConstraint(
        "platform_kind = 'WEB' AND provider_kind = 'WEB_PUSH'",
        name="ck_push_endpoint_platform_provider",
    ),
    sa.CheckConstraint(
        "octet_length(endpoint_ciphertext) BETWEEN 1 AND 16384",
        name="ck_push_endpoint_ciphertext_size",
    ),
    sa.CheckConstraint(
        "endpoint_fingerprint ~ '^[0-9a-f]{64}$'",
        name="ck_push_endpoint_fingerprint",
    ),
    sa.CheckConstraint("state IN ('ACTIVE', 'REVOKED')", name="ck_push_endpoint_state"),
    sa.CheckConstraint("version >= 1", name="ck_push_endpoint_version"),
    sa.CheckConstraint("last_seen_at >= registered_at", name="ck_push_endpoint_times"),
    sa.CheckConstraint(
        "(state = 'ACTIVE' AND revoked_at IS NULL) OR "
        "(state = 'REVOKED' AND revoked_at IS NOT NULL AND revoked_at >= registered_at)",
        name="ck_push_endpoint_revoked_at",
    ),
    sa.CheckConstraint(
        "app_version IS NULL OR app_version ~ '^[!-~]{1,64}$'",
        name="ck_push_endpoint_app_version",
    ),
)

sa.Index(
    "uq_push_endpoint_active_provider_fingerprint",
    PUSH_ENDPOINTS.c.provider_kind,
    PUSH_ENDPOINTS.c.endpoint_fingerprint,
    unique=True,
    postgresql_where=sa.text("state = 'ACTIVE'"),
)
sa.Index(
    "ix_push_endpoint_recipient_state",
    PUSH_ENDPOINTS.c.recipient_account_id,
    PUSH_ENDPOINTS.c.state,
)

PUSH_DELIVERIES = sa.Table(
    "push_deliveries",
    METADATA,
    sa.Column("delivery_id", sa.String(36), primary_key=True),
    sa.Column(
        "inbox_item_id",
        sa.String(36),
        sa.ForeignKey(
            "notifications.inbox_items.inbox_item_id",
            name="fk_push_delivery_inbox_item",
            ondelete="RESTRICT",
        ),
        nullable=False,
    ),
    sa.Column(
        "push_endpoint_id",
        sa.String(36),
        sa.ForeignKey(
            "notifications.push_endpoints.push_endpoint_id",
            name="fk_push_delivery_endpoint",
            ondelete="RESTRICT",
        ),
        nullable=False,
    ),
    sa.Column("recipient_account_id", sa.String(36), nullable=False),
    sa.Column("status", sa.String(16), server_default=sa.text("'PENDING'"), nullable=False),
    sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
    sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("last_attempt_at", sa.DateTime(timezone=True)),
    sa.Column("last_error_code", sa.String(24)),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.Column("completed_at", sa.DateTime(timezone=True)),
    sa.UniqueConstraint("inbox_item_id", "push_endpoint_id", name="uq_push_delivery_item_endpoint"),
    sa.CheckConstraint(
        "status IN ('PENDING', 'SENT', 'FAILED', 'DEAD_ENDPOINT', 'SKIPPED')",
        name="ck_push_delivery_status",
    ),
    sa.CheckConstraint("attempt_count BETWEEN 0 AND 5", name="ck_push_delivery_attempts"),
    sa.CheckConstraint(
        "last_error_code IS NULL OR last_error_code IN "
        "('TRANSIENT', 'TIMEOUT', 'RATE_LIMITED', 'ENDPOINT_GONE', 'REJECTED', 'SENDER_ERROR')",
        name="ck_push_delivery_error",
    ),
    sa.CheckConstraint(
        "(status = 'PENDING' AND completed_at IS NULL) OR "
        "(status <> 'PENDING' AND completed_at IS NOT NULL)",
        name="ck_push_delivery_completed",
    ),
    sa.CheckConstraint(
        "(last_attempt_at IS NULL OR last_attempt_at >= created_at) "
        "AND (completed_at IS NULL OR completed_at >= created_at)",
        name="ck_push_delivery_times",
    ),
)

sa.Index(
    "ix_push_delivery_due",
    PUSH_DELIVERIES.c.next_attempt_at,
    PUSH_DELIVERIES.c.push_endpoint_id,
    PUSH_DELIVERIES.c.created_at,
    PUSH_DELIVERIES.c.delivery_id,
    postgresql_where=sa.text("status = 'PENDING'"),
)
sa.Index(
    "ix_push_delivery_endpoint_pending",
    PUSH_DELIVERIES.c.push_endpoint_id,
    PUSH_DELIVERIES.c.created_at,
    PUSH_DELIVERIES.c.delivery_id,
    postgresql_where=sa.text("status = 'PENDING'"),
)
