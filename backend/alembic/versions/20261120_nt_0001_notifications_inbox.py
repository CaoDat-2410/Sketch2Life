"""DDL-C (part 1 of 2): the notification inbox ``notifications.inbox_items``.

FEAT-066 goal v3, T-8a (SRS l.784, l.812, l.1681; FR-B-09; UC-15; REG l.403-405, l.466). The inbox
is the source of truth of a notification: a row is written once by a producer (the typed
``NotificationCommandV1``), read by its recipient and marked read. Nothing is delivered from here
(no e-mail, no push, no provider).

Package scope. DDL-C is approved by name with three tables (OD-01). This revision creates only
``inbox_items`` (plan review R1: a strict subset of the package). ``push_endpoints`` and
``delivery_attempts`` belong to T-8b, which is deferred; they are not created, stubbed or mirrored
here, and a later revision for them is a child of this one.

Design points proved on PostgreSQL by ``tests/integration/test_t8a_notifications_postgres.py``:

* ``recipient_account_id`` is the opaque ``be1_adult_identities.account_id``; no cross-owner
  foreign key, no e-mail, no identity-provider subject.
* ``(recipient_account_id, trigger_dedupe_key)`` is unique (the producer dedupe); ``command_sha256``
  lets the producer tell a replay (same hash) from a clash (other hash).
* ``safe_parameters`` is a JSON object of codes, counts and opaque refs. The database caps its
  size and shape; the allowlist that keeps a name or a sentence out is enforced by the producer
  (the only writer). No column holds a child name, media, a playback URL, an endpoint or a token.
* ``read_at >= created_at`` and ``expires_at > created_at`` (the producer passes ``created_at``
  from its own clock, so the check is not exposed to clock skew between app and database).

It extends the ``lesson_library`` branch (parent ``20261120_cls_0002``, the only child of it); it
adds no branch label. Heads stay 14 (10 with ``depends_on``). The downgrade refuses while any inbox
row exists and never deletes silently. Run it with an explicit target, never ``-1`` (many heads):
``alembic downgrade 20261120_cls_0002`` and ``alembic upgrade heads``. Never run against
``sketch2life_m2_s1a``, ``be1_acceptance`` or ports 5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261120_nt_0001"
down_revision = "20261120_cls_0002"
branch_labels = None
depends_on = None

SCHEMA = "notifications"
TABLE = "inbox_items"
DEDUPE_CONSTRAINT = "uq_notif_inbox_dedupe"
PAGE_INDEX = "ix_notif_inbox_page"
UNREAD_INDEX = "ix_notif_inbox_unread"
UNREAD_WHERE = "read_at IS NULL"

ROLE_CHECK = "recipient_role IN ('parent', 'teacher', 'school_manager', 'platform_admin')"
TYPE_CHECK = "notification_type ~ '^[A-Z][A-Z0-9_]{2,63}$'"
TEMPLATE_CHECK = "template_version BETWEEN 1 AND 9999"
KEYS_CHECK = (
    "trigger_id ~ '^[A-Za-z0-9._:-]{1,128}$' AND trigger_dedupe_key ~ '^[A-Za-z0-9._:-]{1,128}$'"
)
HASH_CHECK = "command_sha256 ~ '^[0-9a-f]{64}$'"
PARAMS_CHECK = (
    "jsonb_typeof(safe_parameters) = 'object' AND octet_length(safe_parameters::text) <= 2048"
)
TIMES_CHECK = (
    "(read_at IS NULL OR read_at >= created_at) AND (expires_at IS NULL OR expires_at > created_at)"
)

DOWNGRADE_GUARD = """
DO $nt_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM notifications.inbox_items) THEN
        RAISE EXCEPTION 'DDL-C part 1 downgrade refused - inbox rows exist';
    END IF;
END;
$nt_downgrade_guard$;
"""


def upgrade() -> None:
    op.execute(sa.schema.CreateSchema(SCHEMA, if_not_exists=True))
    # Preserve rows from the earlier Parent platform inbox before creating the richer T-8a inbox.
    op.execute(
        sa.text(
            """
            DO $legacy_platform_inbox$
            BEGIN
                IF to_regclass('notifications.platform_inbox_items') IS NULL
                   AND to_regclass('notifications.inbox_items') IS NOT NULL
                   AND EXISTS (
                       SELECT 1 FROM information_schema.columns
                       WHERE table_schema = 'notifications'
                         AND table_name = 'inbox_items'
                         AND column_name = 'notification_id'
                   ) THEN
                    ALTER TABLE notifications.inbox_items
                        RENAME TO platform_inbox_items;
                END IF;
            END;
            $legacy_platform_inbox$;
            """
        )
    )
    op.create_table(
        TABLE,
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
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("recipient_account_id", "trigger_dedupe_key", name=DEDUPE_CONSTRAINT),
        sa.CheckConstraint(ROLE_CHECK, name="ck_notif_inbox_role"),
        sa.CheckConstraint(TYPE_CHECK, name="ck_notif_inbox_type"),
        sa.CheckConstraint(TEMPLATE_CHECK, name="ck_notif_inbox_template"),
        sa.CheckConstraint(KEYS_CHECK, name="ck_notif_inbox_keys"),
        sa.CheckConstraint(HASH_CHECK, name="ck_notif_inbox_hash"),
        sa.CheckConstraint(PARAMS_CHECK, name="ck_notif_inbox_params"),
        sa.CheckConstraint(TIMES_CHECK, name="ck_notif_inbox_times"),
        schema=SCHEMA,
    )
    op.create_index(
        PAGE_INDEX,
        TABLE,
        ["recipient_account_id", sa.text("created_at DESC"), sa.text("inbox_item_id DESC")],
        schema=SCHEMA,
    )
    op.create_index(
        UNREAD_INDEX,
        TABLE,
        ["recipient_account_id"],
        schema=SCHEMA,
        postgresql_where=sa.text(UNREAD_WHERE),
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.drop_index(UNREAD_INDEX, table_name=TABLE, schema=SCHEMA)
    op.drop_index(PAGE_INDEX, table_name=TABLE, schema=SCHEMA)
    op.drop_table(TABLE, schema=SCHEMA)
    op.execute(sa.schema.DropSchema(SCHEMA))
