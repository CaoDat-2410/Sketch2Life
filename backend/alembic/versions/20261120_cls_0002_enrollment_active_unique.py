"""DDL-H (part 2): one active enrollment per child, kept history of closed enrollments.

FEAT-066 goal v3, T-7d (enrollment move between classes, SRS l.544, l.1651, l.1426; REG l.102,
l.248, l.273). The Teacher move closes the source enrollment (``state = 'withdrawn'``, the row is
kept) and opens a new ``active`` row in the target class, so a child can return to a class it left
and the history reads ``A withdrawn, B withdrawn, A active``. The unique constraint
``uq_be1_enrollment (organization_id, class_id, child_id)`` forbids the second row for the same
class, and nothing enforces "one active enrollment per child" in the database. This revision
swaps them:

* the full unique constraint is dropped and replaced by a plain lookup index
  ``ix_be1_enrollment_class_child`` (the same columns, the same lookups);
* a partial unique index ``uq_be1_enrollment_active (organization_id, child_id) WHERE
  state = 'active'`` holds the one-active rule in the database (``child_id`` is the global primary
  key of ``be1_managed_profiles``).

It extends the ``lesson_library`` branch (parent ``20261120_cls_0001``, the T-7b class revision);
it adds no branch label and creates no table. Both guards refuse loudly and delete nothing.

Upgrade: refuses while a child already holds more than one active enrollment (the partial unique
index could not be built). Downgrade: refuses while any ``(organization, class, child)`` has more
than one enrollment row, that is, after a child returned to a class it left (the old unique
constraint could not be rebuilt). In that case keep the partial index.

Run the downgrade with an explicit target, never ``-1``: the graph has many heads and ``-1`` picks
an unrelated one. Use ``alembic downgrade 20261120_cls_0001`` and ``alembic upgrade heads``.
Never run against ``sketch2life_m2_s1a``, ``be1_acceptance`` or ports 5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261120_cls_0002"
down_revision = "20261120_cls_0001"
branch_labels = None
depends_on = None

TABLE = "be1_enrollments"
OLD_UNIQUE = "uq_be1_enrollment"
LOOKUP_INDEX = "ix_be1_enrollment_class_child"
ACTIVE_UNIQUE_INDEX = "uq_be1_enrollment_active"
LOOKUP_COLUMNS = ["organization_id", "class_id", "child_id"]
ACTIVE_COLUMNS = ["organization_id", "child_id"]
ACTIVE_WHERE = "state = 'active'"

UPGRADE_GUARD = """
DO $enr_upgrade_guard$
BEGIN
    IF EXISTS (
        SELECT 1 FROM be1_enrollments WHERE state = 'active'
        GROUP BY organization_id, child_id HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'DDL-H part 2 upgrade refused - a child has several active enrollments';
    END IF;
END;
$enr_upgrade_guard$;
"""

DOWNGRADE_GUARD = """
DO $enr_downgrade_guard$
BEGIN
    IF EXISTS (
        SELECT 1 FROM be1_enrollments
        GROUP BY organization_id, class_id, child_id HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'DDL-H part 2 downgrade refused - a child returned to a former class';
    END IF;
END;
$enr_downgrade_guard$;
"""


def upgrade() -> None:
    op.execute(sa.text(UPGRADE_GUARD))
    op.drop_constraint(OLD_UNIQUE, TABLE, type_="unique")
    op.create_index(LOOKUP_INDEX, TABLE, LOOKUP_COLUMNS)
    op.create_index(
        ACTIVE_UNIQUE_INDEX,
        TABLE,
        ACTIVE_COLUMNS,
        unique=True,
        postgresql_where=sa.text(ACTIVE_WHERE),
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.drop_index(ACTIVE_UNIQUE_INDEX, table_name=TABLE)
    op.drop_index(LOOKUP_INDEX, table_name=TABLE)
    op.create_unique_constraint(OLD_UNIQUE, TABLE, LOOKUP_COLUMNS)
