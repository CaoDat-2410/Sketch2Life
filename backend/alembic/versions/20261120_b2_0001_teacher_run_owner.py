"""DDL-B2: the Teacher owner, the occurrence pin and the Teacher lock on ``story.runs``.

FEAT-066 goal v3, T-4b2 (``POST /v1/story-runs`` for a Teacher; SRS BR-02 l.246, FR-C-03 l.495,
l.1020, l.1349, l.351, l.1448; REG l.373). The owner approved this extension by name, and exactly
this list (goal log): the Teacher lock ``active_owner_teacher_id`` (with its unique index, the
lock-state CHECK and the release trigger), ``occurrence_ref`` and ``created_by_actor_ref`` (the
latter separate from the active owner: provenance only, l.553), the per-occurrence unique index (one
successful sample, l.351) and the pins CHECK (a run is bound to exactly one child, occurrence and
approved plan, l.1448). Nothing else changes: no existing column, no existing CHECK, no table.

Upgrade, on ``story.runs`` only:

* three nullable ``varchar(36)`` columns: ``active_owner_teacher_id`` (the Teacher account that
  holds the run lock; ``active_owner_parent_account_id`` stays the Parent one),
  ``occurrence_ref`` (the lesson occurrence the run was created for; an opaque ref, no foreign key:
  DDL-A forbids deleting an occurrence) and ``created_by_actor_ref`` (who created the run; never
  grants access);
* ``ck_story_run_teacher_pins``: ``occurrence_ref`` and ``created_by_actor_ref`` are set together or
  not at all (a Parent run keeps both NULL, a recorded choice: REG gives ``created_by_actor_ref`` to
  every run, but no Parent writer sets it);
* ``ck_story_run_teacher_owner``: a Teacher lock needs an occurrence, the ``ORGANIZATION`` scope and
  no Parent lock;
* ``ck_story_run_teacher_lock_state``: a run in ``COMPLETED``, ``FAILED``, ``ABANDONED``,
  ``DELETE_PENDING`` or ``DELETED`` holds no Teacher lock (``SAFETY_BLOCKED`` is an adult-wait state
  and keeps it, l.394);
* the unique partial indexes ``uq_story_run_active_teacher`` (one active run per Teacher, BR-02) and
  ``uq_story_run_active_occurrence`` (one active Teacher run per occurrence) and the lookup index
  ``ix_story_run_occurrence``;
* ``story.release_teacher_lock()`` and the trigger ``trg_story_run_release_teacher_lock``
  (``BEFORE UPDATE OF run_state``): moving a run to one of the five lock-free states clears the
  Teacher lock, so every present and future writer (cancel, delete, failure, closeout, Complete)
  releases it without editing each site (the Parent lock stays released by those writers).

Terminal list: it equals the five states of ``ck_story_run_state`` that hold no lock (l.394); a
state added by a later task must be classified here and in the CHECK together.

``frc08_lifecycle`` branch: parent ``20261120_vb_0002`` (the only head of the Story chain). Heads
stay 14 (10 with ``depends_on``). The downgrade refuses while any run row holds one of the new
columns and never deletes silently. Run it with an explicit target, never ``-1`` (many heads), on
a disposable database only: ``alembic downgrade 20261120_vb_0002``, then ``alembic upgrade heads``.
Never run against ``sketch2life_m2_s1a`` or ports 5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261120_b2_0001"
down_revision = "20261120_vb_0002"
branch_labels = None
depends_on = None

SCHEMA = "story"
TABLE = "runs"
FUNCTION = "release_teacher_lock"
TRIGGER = "trg_story_run_release_teacher_lock"
LOCK_FREE_STATES = "'COMPLETED','FAILED','ABANDONED','DELETE_PENDING','DELETED'"

COLUMNS = ("active_owner_teacher_id", "occurrence_ref", "created_by_actor_ref")

CHECKS: tuple[tuple[str, str], ...] = (
    ("ck_story_run_teacher_pins", "(occurrence_ref IS NULL) = (created_by_actor_ref IS NULL)"),
    (
        "ck_story_run_teacher_owner",
        "active_owner_teacher_id IS NULL OR (occurrence_ref IS NOT NULL "
        "AND actor_scope_kind = 'ORGANIZATION' AND active_owner_parent_account_id IS NULL)",
    ),
    (
        "ck_story_run_teacher_lock_state",
        f"active_owner_teacher_id IS NULL OR run_state NOT IN ({LOCK_FREE_STATES})",
    ),
)

INDEXES: tuple[tuple[str, str, str | None], ...] = (
    (
        "uq_story_run_active_teacher",
        "active_owner_teacher_id",
        "active_owner_teacher_id IS NOT NULL",
    ),
    ("uq_story_run_active_occurrence", "occurrence_ref", "active_owner_teacher_id IS NOT NULL"),
    ("ix_story_run_occurrence", "occurrence_ref", "occurrence_ref IS NOT NULL"),
)

FUNCTION_SQL = f"""
CREATE FUNCTION {SCHEMA}.{FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.active_owner_teacher_id IS NOT NULL
     AND NEW.run_state IN ({LOCK_FREE_STATES}) THEN
    NEW.active_owner_teacher_id := NULL;
  END IF;
  RETURN NEW;
END;
$$;
"""

DOWNGRADE_GUARD = f"""
DO $b2_downgrade_guard$
BEGIN
    IF EXISTS (
        SELECT 1 FROM {SCHEMA}.{TABLE}
        WHERE active_owner_teacher_id IS NOT NULL
           OR occurrence_ref IS NOT NULL
           OR created_by_actor_ref IS NOT NULL
    ) THEN
        RAISE EXCEPTION 'T-4b2 downgrade refused - Teacher run rows exist';
    END IF;
END;
$b2_downgrade_guard$;
"""


def upgrade() -> None:
    for column in COLUMNS:
        op.add_column(TABLE, sa.Column(column, sa.String(36)), schema=SCHEMA)
    for name, text in CHECKS:
        op.create_check_constraint(name, TABLE, text, schema=SCHEMA)
    for name, column, predicate in INDEXES:
        op.create_index(
            name,
            TABLE,
            [column],
            unique=name.startswith("uq_"),
            schema=SCHEMA,
            postgresql_where=sa.text(predicate) if predicate else None,
        )
    op.execute(FUNCTION_SQL)
    op.execute(
        f"CREATE TRIGGER {TRIGGER} BEFORE UPDATE OF run_state ON {SCHEMA}.{TABLE} "
        f"FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.{FUNCTION}()"
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.execute(f"DROP TRIGGER {TRIGGER} ON {SCHEMA}.{TABLE}")
    op.execute(f"DROP FUNCTION {SCHEMA}.{FUNCTION}()")
    for name, _column, _predicate in reversed(INDEXES):
        op.drop_index(name, table_name=TABLE, schema=SCHEMA)
    for name, _text in reversed(CHECKS):
        op.drop_constraint(name, TABLE, schema=SCHEMA, type_="check")
    for column in reversed(COLUMNS):
        op.drop_column(TABLE, column, schema=SCHEMA)
