"""DDL-H (part 1): the stored class revision counter ``be1_classrooms.revision``.

FEAT-066 goal v3, T-7b (class archive and manual suspend, SRS l.1651, l.1699, l.1709; TD-28). It
extends the ``lesson_library`` branch (parent ``20261119_oc_0001``); it adds no branch label and
creates no table. The package DDL-H was drafted as a class-state CHECK; that CHECK is not needed
(``be1_classrooms.state`` has no CHECK, so ``suspended`` and ``archived`` are storable today), so
the package is re-scoped to the class revision column (T-7b) and the enrollment active-uniqueness
of T-7d (a later migration). The coordinator recorded the re-scope in the goal log.

Upgrade: ``revision`` ``INTEGER NOT NULL DEFAULT 1`` and ``ck_be1_class_revision CHECK
(revision > 0)`` (the naming of ``ck_be1_session_revision``). The constant default is
metadata-only on PostgreSQL 11 and later, so there is no table rewrite and no backfill: every
existing class starts at 1.

The counter changes on a state change, on a Teacher assignment and, in T-7d, on an enrollment
move; the application increments it, never a trigger.

Downgrade refuses while any class has ``revision > 1`` (the counter would reset to 1 on a later
re-upgrade and an old ``If-Match`` could match again). Otherwise it drops the constraint and the
column. Run it with an explicit target, never ``-1``: the graph has many heads and ``-1`` picks an
unrelated one. Use ``alembic downgrade 20261119_oc_0001`` and ``alembic upgrade heads``. The ORM
column lives on a ``be1_core`` table but this migration is on the ``lesson_library`` chain, so
``upgrade heads`` (not a per-branch upgrade) is required before the API runs. Never run against
``sketch2life_m2_s1a``, ``be1_acceptance`` or ports 5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261120_cls_0001"
down_revision = "20261119_oc_0001"
branch_labels = None
depends_on = None

TABLE = "be1_classrooms"
CHECK_NAME = "ck_be1_class_revision"
CHECK_TEXT = "revision > 0"

DOWNGRADE_GUARD = """
DO $cls_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM be1_classrooms WHERE revision > 1) THEN
        RAISE EXCEPTION 'DDL-H downgrade refused: a class revision above 1 would be lost';
    END IF;
END;
$cls_downgrade_guard$;
"""


def upgrade() -> None:
    op.add_column(
        TABLE,
        sa.Column("revision", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    op.create_check_constraint(CHECK_NAME, TABLE, CHECK_TEXT)


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.drop_constraint(CHECK_NAME, TABLE, type_="check")
    op.drop_column(TABLE, "revision")
