"""Add declined parent-group invitations and membership read indexes.

Goal v4 Phase C T-10c. Declines remain durable membership history; downgrades are refused while
any declined row would be made invalid by restoring the prior state constraint.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261121_pg_0001"
down_revision = "20261121_ll_0001"
branch_labels = None
depends_on = None

TABLE = "be1_parent_group_members"
STATE_CHECK = "ck_be1_parent_group_member_state"
SELF_PAGE_INDEX = "ix_be1_parent_member_owner_page"
GROUP_PAGE_INDEX = "ix_be1_parent_member_group_page"

DOWNGRADE_GUARD_SQL = f"""
DO $pg_t10c_downgrade_guard$
BEGIN
  IF EXISTS (SELECT 1 FROM {TABLE} WHERE state = 'declined') THEN
    RAISE EXCEPTION 'DDL-P T-10c downgrade refused: declined parent-group membership rows exist';
  END IF;
END;
$pg_t10c_downgrade_guard$;
"""


def upgrade() -> None:
    op.drop_constraint(STATE_CHECK, TABLE, type_="check")
    op.create_check_constraint(
        STATE_CHECK,
        TABLE,
        "state IN ('invited', 'active', 'revoked', 'expired', 'declined')",
    )
    op.create_index(
        SELF_PAGE_INDEX,
        TABLE,
        [
            "parent_principal_ref",
            "state",
            sa.text("invited_at DESC"),
            sa.text("membership_id DESC"),
        ],
    )
    op.create_index(
        GROUP_PAGE_INDEX,
        TABLE,
        [
            "parent_group_id",
            "state",
            sa.text("invited_at DESC"),
            sa.text("membership_id DESC"),
        ],
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD_SQL))
    op.drop_index(GROUP_PAGE_INDEX, table_name=TABLE)
    op.drop_index(SELF_PAGE_INDEX, table_name=TABLE)
    op.drop_constraint(STATE_CHECK, TABLE, type_="check")
    op.create_check_constraint(
        STATE_CHECK,
        TABLE,
        "state IN ('invited', 'active', 'revoked', 'expired')",
    )
