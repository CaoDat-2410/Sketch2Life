"""DDL-B4 fix: allow GENERATE_ACTIVITY_SET receipts again.

``20261125_as_0002`` added ``GENERATE_ACTIVITY_SET`` to ``ck_story_receipt_operation``, but
``20261122_t6b_0002`` and ``20261122_t6c_0001`` follow it in the chain and recreate the check from
lists that do not contain it. On PostgreSQL every Parent activity suggestion request then failed.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261126_as_0003"
down_revision = "20261122_t6c_0001"
branch_labels = None
depends_on = None

SCHEMA = "story"
RECEIPTS = "command_receipts"
CONSTRAINT = "ck_story_receipt_operation"

RECEIPT_OPERATIONS_BEFORE = (
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
    "TRANSFER_TEACHER_OWNER",
    "FORCE_CLOSE_RUN",
)
RECEIPT_OPERATIONS_AFTER = (
    *RECEIPT_OPERATIONS_BEFORE[:14],
    "GENERATE_ACTIVITY_SET",
    *RECEIPT_OPERATIONS_BEFORE[14:],
)

DOWNGRADE_GUARD = f"""
DO $as_0003_downgrade_guard$
BEGIN
    IF EXISTS (
        SELECT 1 FROM {SCHEMA}.{RECEIPTS}
        WHERE operation = 'GENERATE_ACTIVITY_SET'
    ) THEN
        RAISE EXCEPTION 'as_0003 downgrade refused - activity set receipts exist';
    END IF;
END;
$as_0003_downgrade_guard$;
"""


def _replace_check(operations: tuple[str, ...]) -> None:
    values = ",".join(f"'{operation}'" for operation in operations)
    # IF EXISTS: some local databases had this constraint repaired by hand before this revision.
    op.execute(f"ALTER TABLE {SCHEMA}.{RECEIPTS} DROP CONSTRAINT IF EXISTS {CONSTRAINT}")
    op.create_check_constraint(CONSTRAINT, RECEIPTS, f"operation IN ({values})", schema=SCHEMA)


def upgrade() -> None:
    _replace_check(RECEIPT_OPERATIONS_AFTER)


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    _replace_check(RECEIPT_OPERATIONS_BEFORE)


__all__ = [
    "DOWNGRADE_GUARD",
    "RECEIPT_OPERATIONS_AFTER",
    "RECEIPT_OPERATIONS_BEFORE",
]
