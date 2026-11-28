"""DDL-B4: immutable Parent activity suggestion sets and generation receipts."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261125_as_0002"
down_revision = "20261123_ppg_0001"
branch_labels = None
depends_on = None

SCHEMA = "story"
TABLE = "activity_suggestion_sets"
FUNCTION = "forbid_activity_suggestion_set_update"
TRIGGER = "trg_story_activity_suggestion_set_append_only"

NEW_RECEIPT_OPERATIONS = "'GENERATE_ACTIVITY_SET'"
FINAL_RECEIPT_OPERATIONS = (
    "'CREATE_RUN','ATTACH_ASSET','CONFIRM_SUBJECT','CONFIRM_CONTEXT','CANCEL_RUN',"
    "'GENERATE_STORY_REVISION','CONFIRM_STORY_REVISION','DELETE_RUN','SUBMIT_IDEA',"
    "'CONFIRM_TRANSCRIPT','CREATE_VIDEO_GENERATION','MARK_VIDEO_UNSUITABLE',"
    "'COMPLETE_RUN','SELECT_ACTIVITY','GENERATE_ACTIVITY_SET','TRANSFER_TEACHER_OWNER',"
    "'FORCE_CLOSE_RUN'"
)
RECEIPT_OPERATIONS_BEFORE = FINAL_RECEIPT_OPERATIONS
RECEIPT_OPERATIONS_AFTER = FINAL_RECEIPT_OPERATIONS

FUNCTION_SQL = f"""
CREATE FUNCTION {SCHEMA}.{FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'ACTIVITY_SUGGESTION_SET_UPDATE_FORBIDDEN';
END;
$$
"""

DOWNGRADE_GUARD = f"""
DO $as_suggestion_set_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM {SCHEMA}.{TABLE}) THEN
        RAISE EXCEPTION 'DDL-B4 downgrade refused: activity suggestion sets exist';
    END IF;
    IF EXISTS (SELECT 1 FROM {SCHEMA}.command_receipts
               WHERE operation = {NEW_RECEIPT_OPERATIONS}) THEN
        RAISE EXCEPTION 'DDL-B4 downgrade refused: GENERATE_ACTIVITY_SET receipts exist';
    END IF;
END;
$as_suggestion_set_downgrade_guard$;
"""


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("suggestion_set_id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("story.runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("set_revision", sa.Integer, nullable=False),
        sa.Column("understanding_revision", sa.Integer, nullable=False),
        sa.Column("input_revision", sa.Integer, nullable=False),
        sa.Column("context_revision", sa.Integer, nullable=False),
        sa.Column("selection_mode", sa.String(32), nullable=False),
        sa.Column("catalog_candidate_count", sa.Integer, nullable=False),
        sa.Column("activities_snapshot", postgresql.JSONB, nullable=False),
        sa.Column("activities_snapshot_sha256", sa.String(64), nullable=False),
        sa.Column("provider_call_id", sa.String(128)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("run_id", "set_revision", name="uq_ass_run_set_revision"),
        sa.UniqueConstraint(
            "run_id", "suggestion_set_id", name="uq_ass_run_suggestion_set"
        ),
        sa.CheckConstraint("set_revision >= 1", name="ck_ass_set_revision"),
        sa.CheckConstraint(
            "understanding_revision >= 1", name="ck_ass_understanding_revision"
        ),
        sa.CheckConstraint("input_revision >= 1", name="ck_ass_input_revision"),
        sa.CheckConstraint("context_revision >= 1", name="ck_ass_context_revision"),
        sa.CheckConstraint(
            "selection_mode IN ('CATALOG_SELECTION','AI_GENERATED_FALLBACK')",
            name="ck_ass_selection_mode",
        ),
        sa.CheckConstraint(
            "catalog_candidate_count BETWEEN 0 AND 500", name="ck_ass_catalog_count"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(activities_snapshot) = 'array' AND "
            "jsonb_array_length(activities_snapshot) BETWEEN 1 AND 24",
            name="ck_ass_snapshot_shape",
        ),
        sa.CheckConstraint(
            "octet_length(activities_snapshot::text) <= 262144",
            name="ck_ass_snapshot_bound",
        ),
        sa.CheckConstraint(
            "length(activities_snapshot_sha256) = 64", name="ck_ass_snapshot_hash"
        ),
        sa.CheckConstraint(
            "provider_call_id IS NULL OR length(provider_call_id) <= 128",
            name="ck_ass_provider_call_id",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_ass_run_understanding_revision",
        TABLE,
        ["run_id", "understanding_revision", "set_revision"],
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
        f"operation IN ({FINAL_RECEIPT_OPERATIONS})",
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
    op.drop_index("ix_ass_run_understanding_revision", table_name=TABLE, schema=SCHEMA)
    op.drop_table(TABLE, schema=SCHEMA)
