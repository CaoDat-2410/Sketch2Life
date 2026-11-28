"""T-6c DDL: add the Manager force-close Story receipt operation and guard it as append-only."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261122_t6c_0001"
down_revision = "20261122_t6b_0002"
branch_labels = None
depends_on = None

SCHEMA = "story"
RECEIPTS = "command_receipts"
FUNCTION = "guard_force_close_receipt_immutable"
TRIGGER = "trg_story_force_close_receipt_immutable"

FINAL_RECEIPT_OPERATIONS = (
    "CREATE_RUN",
    "ATTACH_ASSET",
    "CONFIRM_SUBJECT",
    "CONFIRM_CONTEXT",
    "CANCEL_RUN",
    "GENERATE_STORY_REVISION",
    "CONFIRM_STORY_REVISION",
    "DELETE_RUN",
    "SUBMIT_IDEA",
    "CONFIRM_TRANSCRIPT",
    "CREATE_VIDEO_GENERATION",
    "MARK_VIDEO_UNSUITABLE",
    "COMPLETE_RUN",
    "SELECT_ACTIVITY",
    "GENERATE_ACTIVITY_SET",
    "TRANSFER_TEACHER_OWNER",
    "FORCE_CLOSE_RUN",
)
RECEIPT_OPERATIONS_BEFORE = FINAL_RECEIPT_OPERATIONS
RECEIPT_OPERATIONS_AFTER = FINAL_RECEIPT_OPERATIONS


def _receipt_operation_check(operations: tuple[str, ...]) -> str:
    values = ",".join(f"'{operation}'" for operation in operations)
    return f"operation IN ({values})"


GUARD_SQL = f"""
CREATE FUNCTION {SCHEMA}.{FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.operation = 'FORCE_CLOSE_RUN' THEN
    RAISE EXCEPTION 'T-6c force-close receipts are append-only'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF NEW.operation = 'FORCE_CLOSE_RUN' THEN
      RAISE EXCEPTION 'T-6c force-close receipts are append-only'
        USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    RETURN NEW;
  END IF;
  RETURN OLD;
END;
$$;
"""

DOWNGRADE_GUARD = f"""
DO $t6c_story_downgrade_guard$
BEGIN
    IF EXISTS (
        SELECT 1 FROM {SCHEMA}.{RECEIPTS}
        WHERE operation = 'FORCE_CLOSE_RUN'
    ) THEN
        RAISE EXCEPTION 'T-6c Story downgrade refused - force-close receipts exist';
    END IF;
END;
$t6c_story_downgrade_guard$;
"""


def upgrade() -> None:
    op.drop_constraint("ck_story_receipt_operation", RECEIPTS, schema=SCHEMA, type_="check")
    op.create_check_constraint(
        "ck_story_receipt_operation",
        RECEIPTS,
        _receipt_operation_check(FINAL_RECEIPT_OPERATIONS),
        schema=SCHEMA,
    )
    op.execute(GUARD_SQL)
    op.execute(
        f"CREATE TRIGGER {TRIGGER} BEFORE UPDATE OR DELETE ON {SCHEMA}.{RECEIPTS} "
        f"FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.{FUNCTION}()"
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.execute(f"DROP TRIGGER {TRIGGER} ON {SCHEMA}.{RECEIPTS}")
    op.execute(f"DROP FUNCTION {SCHEMA}.{FUNCTION}()")
    op.drop_constraint("ck_story_receipt_operation", RECEIPTS, schema=SCHEMA, type_="check")
    op.create_check_constraint(
        "ck_story_receipt_operation",
        RECEIPTS,
        _receipt_operation_check(RECEIPT_OPERATIONS_BEFORE),
        schema=SCHEMA,
    )


__all__ = [
    "DOWNGRADE_GUARD",
    "GUARD_SQL",
    "RECEIPT_OPERATIONS_AFTER",
    "RECEIPT_OPERATIONS_BEFORE",
    "revision",
    "down_revision",
]
