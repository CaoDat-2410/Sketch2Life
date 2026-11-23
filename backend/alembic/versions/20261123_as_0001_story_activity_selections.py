"""DDL-B3: the Parent main-activity selection of a StoryRun and the SELECT_ACTIVITY receipt.

FEAT-066 goal v4, T-2e-a (``GET /v1/activities``,
``POST /v1/story-runs/{run_id}/activity-selection``; SRS l.386, l.394, l.514, l.1412, l.1667;
REG l.373). The package is approved by name (owner decision B1, DDL-B3). It extends the Story chain
on its own branch: the parent is ``20261120_b2_0001`` (DDL-B2), the only head of that chain, which
this revision replaces as its head (the label is inherited, so none is declared and ``depends_on``
is not used). Alembic heads stay 15 down-only (10 dependency-aware).

Upgrade, in order:

1. ``story.activity_selections``: one row per selection of the main activity of one run,
   append-only. A row names the lesson activity by its exact version and content hash and keeps a
   bounded snapshot of the activity text, so a later lesson edit or unpublish does not change what
   the adult chose (the snapshot is lesson content copied into Story, so the FR-C-08 purge deletes
   it explicitly). ``AI_DRAFT`` is reserved for T-2e-b and is not written yet.
2. A ``BEFORE UPDATE`` trigger: a selection row is never changed (a re-selection is a new row with
   the next ``selection_no``). There is no DELETE guard: the purge must delete the rows, and the
   run foreign key is ``ON DELETE CASCADE`` for hygiene only.
3. ``ck_story_receipt_operation`` gains ``SELECT_ACTIVITY`` (13 to 14 values): dropped and
   re-created.

The downgrade refuses while any selection row or any ``SELECT_ACTIVITY`` receipt exists (after a
purge only the receipts remain), restores the 13-name check and drops the table. Run it with an
explicit target, never ``-1`` (the graph has many heads), on a disposable database only:
``alembic downgrade 20261120_b2_0001``, then ``alembic upgrade heads``. Never run against
``sketch2life_m2_s1a`` or ports 5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261123_as_0001"
down_revision = "20261120_b2_0001"
branch_labels = None
depends_on = None

SCHEMA = "story"
TABLE = "activity_selections"
FUNCTION = "forbid_activity_selection_update"
TRIGGER = "trg_story_activity_selection_append_only"

NEW_RECEIPT_OPERATIONS = "'SELECT_ACTIVITY'"
RECEIPT_OPERATIONS_BEFORE = (
    "'CREATE_RUN','ATTACH_ASSET','CONFIRM_SUBJECT','CONFIRM_CONTEXT',"
    "'CANCEL_RUN','GENERATE_STORY_REVISION','CONFIRM_STORY_REVISION','DELETE_RUN',"
    "'SUBMIT_IDEA','CONFIRM_TRANSCRIPT','CREATE_VIDEO_GENERATION',"
    "'MARK_VIDEO_UNSUITABLE','COMPLETE_RUN'"
)
RECEIPT_OPERATIONS_AFTER = f"{RECEIPT_OPERATIONS_BEFORE},{NEW_RECEIPT_OPERATIONS}"

CHECKS: tuple[tuple[str, str], ...] = (
    ("ck_as_selection_no", "selection_no >= 1"),
    ("ck_as_target_revision", "target_understanding_revision >= 1"),
    ("ck_as_source_kind", "source_kind IN ('LESSON_ACTIVITY','AI_DRAFT')"),
    (
        "ck_as_shape",
        "(source_kind = 'LESSON_ACTIVITY' AND lesson_id IS NOT NULL AND version_id IS NOT NULL "
        "AND content_sha256 IS NOT NULL AND length(content_sha256) = 64 "
        "AND activity_index IS NOT NULL AND activity_index >= 0) OR "
        "(source_kind = 'AI_DRAFT' AND lesson_id IS NULL AND version_id IS NULL "
        "AND content_sha256 IS NULL AND activity_index IS NULL)",
    ),
    ("ck_as_snapshot_bound", "octet_length(activity_snapshot::text) <= 32768"),
    ("ck_as_snapshot_hash", "length(activity_snapshot_sha256) = 64"),
    ("ck_as_actor_kind", "actor_scope_kind IN ('PARENT_ACCOUNT','ORGANIZATION')"),
)

FUNCTION_SQL = f"""
CREATE FUNCTION {SCHEMA}.{FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'ACTIVITY_SELECTION_UPDATE_FORBIDDEN';
END;
$$
"""

DOWNGRADE_GUARD = f"""
DO $as_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM {SCHEMA}.{TABLE}) THEN
        RAISE EXCEPTION 'DDL-B3 downgrade refused: activity selections exist';
    END IF;
    IF EXISTS (SELECT 1 FROM {SCHEMA}.command_receipts
               WHERE operation IN ({NEW_RECEIPT_OPERATIONS})) THEN
        RAISE EXCEPTION 'DDL-B3 downgrade refused: SELECT_ACTIVITY receipts exist';
    END IF;
END;
$as_downgrade_guard$;
"""


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("selection_id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("story.runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("selection_no", sa.Integer, nullable=False),
        sa.Column("target_understanding_revision", sa.Integer, nullable=False),
        sa.Column("source_kind", sa.String(24), nullable=False),
        sa.Column("lesson_id", sa.String(36)),
        sa.Column("version_id", sa.String(36)),
        sa.Column("content_sha256", sa.String(64)),
        sa.Column("activity_index", sa.Integer),
        sa.Column("activity_snapshot", postgresql.JSONB, nullable=False),
        sa.Column("activity_snapshot_sha256", sa.String(64), nullable=False),
        sa.Column(
            "command_receipt_id",
            sa.String(36),
            sa.ForeignKey("story.command_receipts.receipt_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("actor_scope_kind", sa.String(32), nullable=False),
        sa.Column("actor_scope_ref", sa.String(128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("run_id", "selection_no", name="uq_as_run_selection_no"),
        sa.UniqueConstraint("command_receipt_id", name="uq_as_command_receipt"),
        schema=SCHEMA,
    )
    for name, expression in CHECKS:
        op.create_check_constraint(name, TABLE, expression, schema=SCHEMA)
    op.create_index(
        "ix_as_run_target",
        TABLE,
        ["run_id", "target_understanding_revision", "selection_no"],
        schema=SCHEMA,
    )
    op.execute(FUNCTION_SQL)
    op.execute(
        f"CREATE TRIGGER {TRIGGER} BEFORE UPDATE ON {SCHEMA}.{TABLE} "
        f"FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.{FUNCTION}()"
    )

    op.drop_constraint(
        "ck_story_receipt_operation", "command_receipts", schema=SCHEMA, type_="check"
    )
    op.create_check_constraint(
        "ck_story_receipt_operation",
        "command_receipts",
        f"operation IN ({RECEIPT_OPERATIONS_AFTER})",
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))

    op.drop_constraint(
        "ck_story_receipt_operation", "command_receipts", schema=SCHEMA, type_="check"
    )
    op.create_check_constraint(
        "ck_story_receipt_operation",
        "command_receipts",
        f"operation IN ({RECEIPT_OPERATIONS_BEFORE})",
        schema=SCHEMA,
    )

    op.execute(f"DROP TRIGGER {TRIGGER} ON {SCHEMA}.{TABLE}")
    op.execute(f"DROP FUNCTION {SCHEMA}.{FUNCTION}()")
    op.drop_index("ix_as_run_target", table_name=TABLE, schema=SCHEMA)
    op.drop_table(TABLE, schema=SCHEMA)
