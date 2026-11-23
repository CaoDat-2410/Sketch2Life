"""DDL-A extension: ``lesson.occurrence_child_selections`` (Teacher random-child selection).

FEAT-066 goal v3, T-4b1 (SRS l.341-352, l.549-554, l.1441, l.1447-1448, AC-56, section 31.10(4);
OD-02). One immutable evidence row per selection outcome of a lesson occurrence: which opaque
profile ref was offered to the responsible Teacher, out of how many eligible candidates, under which
policy version, and the compare-and-set state of the Teacher's confirmation.

Owner approval (by name, four conditions; goal log). The table is metadata only:

* occurrence ref, plan revision ref, organization and class refs, the opaque ``selected_child_ref``,
  the eligible-candidate count and a SHA-256 over the sorted opaque candidate refs, the policy
  version, the actor ref, timestamps, the state and the ``revision`` for compare-and-set;
* NO child name, NO age, NO random seed, NO drawn index and no value that can re-identify the child
  or reproduce the draw (BR-34); nothing of it is written to audit, log or metric labels;
* rows are purged together with the profile by the FR-C-10 deletion path: the DELETE trigger refuses
  every delete unless the transaction-local flag ``sketch2life.child_selection_purge`` is ``on``
  (the purge function sets it; its caller does not exist yet, recorded as OPEN-1);
* the retention period stays OPEN (SRS l.354); there is no expiry-based purge.

Two deltas against the approved Draft 1 design (reviewer ruling, recorded in the evidence note):
the ``seq`` identity column (ordering only) and the DELETE exception under the purge flag.

``lesson_library`` branch: parent ``20261120_nt_0001`` (the only head of the branch). Heads stay 14
(10 with ``depends_on``). The downgrade refuses while the table holds a row and never deletes
silently. Run it with an explicit target, never ``-1`` (many heads), on a disposable database only:
``alembic downgrade 20261120_nt_0001``, then ``alembic upgrade heads``. Never run against
``sketch2life_m2_s1a``, the database of another task or ports 5432/5433.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from alembic import op

revision = "20261120_sel_0001"
down_revision = "20261120_nt_0001"
branch_labels = None
depends_on = None

SCHEMA = "lesson"
TABLE = "occurrence_child_selections"
FUNCTION = "protect_child_selection"
TRIGGER = "protect_child_selection"
PURGE_FLAG = "sketch2life.child_selection_purge"

HEX64 = "'^[0-9a-f]{64}$'"
UUID_PATTERN = "'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'"

CHECKS: tuple[tuple[str, str], ...] = (
    ("ck_sel_id_uuid", f"selection_id ~ {UUID_PATTERN}"),
    ("ck_sel_kind", "kind IN ('DRAW', 'RESELECT', 'REOFFER', 'EMPTY')"),
    (
        "ck_sel_state",
        "state IN ('OPEN', 'CONFIRMED', 'CONSUMED', 'EXPIRED', 'STALE', 'VOID', 'EMPTY')",
    ),
    ("ck_sel_basis", "eligibility_basis = 'SYNTHETIC_DEV'"),
    ("ck_sel_policy", "policy_version ~ '^[a-z0-9][a-z0-9.-]{0,47}$'"),
    ("ck_sel_hash", f"candidate_set_hash ~ {HEX64}"),
    ("ck_sel_revision", "revision >= 1"),
    ("ck_sel_class_revision", "class_revision >= 1 AND occurrence_revision >= 1"),
    (
        "ck_sel_kind_draw",
        "(kind = 'DRAW' AND draw_no = 1) OR (kind = 'RESELECT' AND draw_no = 2) "
        "OR (kind = 'REOFFER' AND draw_no IN (1, 2)) OR (kind = 'EMPTY' AND draw_no IS NULL)",
    ),
    (
        "ck_sel_empty_shape",
        "(kind = 'EMPTY' AND state = 'EMPTY' AND candidate_count = 0 "
        "AND selected_child_ref IS NULL AND expires_at IS NULL) "
        "OR (kind <> 'EMPTY' AND state <> 'EMPTY' AND candidate_count >= 1 "
        "AND selected_child_ref IS NOT NULL AND char_length(selected_child_ref) >= 1 "
        "AND expires_at IS NOT NULL AND expires_at > issued_at)",
    ),
    (
        "ck_sel_confirm_cols",
        "((confirmed_at IS NULL) = (confirmed_by IS NULL)) "
        "AND ((confirmed_at IS NULL) = (confirmation_expires_at IS NULL)) "
        "AND (confirmation_expires_at IS NULL OR confirmation_expires_at > confirmed_at) "
        "AND (state NOT IN ('CONFIRMED', 'CONSUMED') OR confirmed_at IS NOT NULL) "
        "AND (state <> 'OPEN' OR confirmed_at IS NULL)",
    ),
    (
        "ck_sel_consume_cols",
        "((consumed_at IS NULL) = (consumed_run_ref IS NULL)) "
        "AND ((state = 'CONSUMED') = (consumed_at IS NOT NULL))",
    ),
)

# The identity and evidence columns of a row never change after the insert.
FROZEN_COLUMNS: tuple[str, ...] = (
    "seq",
    "selection_id",
    "occurrence_id",
    "plan_revision_id",
    "organization_ref",
    "class_ref",
    "teacher_ref",
    "kind",
    "draw_no",
    "policy_version",
    "eligibility_basis",
    "candidate_count",
    "candidate_set_hash",
    "selected_child_ref",
    "class_revision",
    "occurrence_revision",
    "issued_at",
    "expires_at",
    "created_at",
)


def _row(prefix: str) -> str:
    return "ROW(" + ", ".join(f"{prefix}.{column}" for column in FROZEN_COLUMNS) + ")"


FUNCTION_SQL = f"""
CREATE FUNCTION {SCHEMA}.{FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  occ_org text;
  occ_class text;
BEGIN
  IF TG_OP = 'DELETE' THEN
    IF coalesce(current_setting('{PURGE_FLAG}', true), '') = 'on' THEN
      RETURN OLD;
    END IF;
    RAISE EXCEPTION 'CHILD_SELECTION_DELETE_FORBIDDEN';
  END IF;
  IF TG_OP = 'INSERT' THEN
    IF NEW.revision <> 1 OR NEW.confirmed_at IS NOT NULL OR NEW.confirmed_by IS NOT NULL
       OR NEW.confirmation_expires_at IS NOT NULL OR NEW.consumed_at IS NOT NULL
       OR NEW.consumed_run_ref IS NOT NULL THEN
      RAISE EXCEPTION 'CHILD_SELECTION_INSERT_NOT_FRESH';
    END IF;
    IF NEW.kind = 'EMPTY' THEN
      IF NEW.state <> 'EMPTY' THEN
        RAISE EXCEPTION 'CHILD_SELECTION_INSERT_STATE';
      END IF;
    ELSIF NEW.state <> 'OPEN' THEN
      RAISE EXCEPTION 'CHILD_SELECTION_INSERT_STATE';
    END IF;
    SELECT organization_ref, class_ref INTO occ_org, occ_class
      FROM {SCHEMA}.occurrences WHERE occurrence_id = NEW.occurrence_id;
    IF FOUND AND (occ_org IS DISTINCT FROM NEW.organization_ref
                  OR occ_class IS DISTINCT FROM NEW.class_ref) THEN
      RAISE EXCEPTION 'CHILD_SELECTION_SCOPE_MISMATCH';
    END IF;
    RETURN NEW;
  END IF;
  IF {_row("OLD")} IS DISTINCT FROM {_row("NEW")} THEN
    RAISE EXCEPTION 'CHILD_SELECTION_IMMUTABLE';
  END IF;
  IF NEW.revision <> OLD.revision + 1 THEN
    RAISE EXCEPTION 'CHILD_SELECTION_REVISION';
  END IF;
  IF NOT ((OLD.state = 'OPEN' AND NEW.state IN ('CONFIRMED', 'EXPIRED', 'STALE', 'VOID'))
          OR (OLD.state = 'CONFIRMED' AND NEW.state IN ('CONSUMED', 'EXPIRED', 'STALE', 'VOID')))
  THEN
    RAISE EXCEPTION 'CHILD_SELECTION_STATE_EDGE';
  END IF;
  IF NEW.state = 'CONFIRMED' THEN
    IF OLD.confirmed_at IS NOT NULL OR NEW.confirmed_at IS NULL THEN
      RAISE EXCEPTION 'CHILD_SELECTION_CONFIRM_COLUMNS';
    END IF;
  ELSIF ROW(OLD.confirmed_at, OLD.confirmed_by, OLD.confirmation_expires_at)
        IS DISTINCT FROM ROW(NEW.confirmed_at, NEW.confirmed_by, NEW.confirmation_expires_at) THEN
    RAISE EXCEPTION 'CHILD_SELECTION_CONFIRM_COLUMNS';
  END IF;
  IF NEW.state = 'CONSUMED' THEN
    IF OLD.consumed_at IS NOT NULL OR NEW.consumed_at IS NULL THEN
      RAISE EXCEPTION 'CHILD_SELECTION_CONSUME_COLUMNS';
    END IF;
  ELSIF ROW(OLD.consumed_at, OLD.consumed_run_ref)
        IS DISTINCT FROM ROW(NEW.consumed_at, NEW.consumed_run_ref) THEN
    RAISE EXCEPTION 'CHILD_SELECTION_CONSUME_COLUMNS';
  END IF;
  RETURN NEW;
END;
$$;
"""

DOWNGRADE_GUARD = f"""
DO $sel_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM {SCHEMA}.{TABLE}) THEN
        RAISE EXCEPTION 'T-4b1 downgrade refused - child selection rows exist';
    END IF;
END;
$sel_downgrade_guard$;
"""


def _timestamp() -> sa.DateTime:
    return sa.DateTime(timezone=True)


def _columns() -> list[Any]:
    return [
        sa.Column("seq", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("selection_id", sa.String(36), primary_key=True),
        sa.Column("occurrence_id", sa.String(36), nullable=False),
        sa.Column("plan_revision_id", sa.String(36), nullable=False),
        sa.Column("organization_ref", sa.String(128), nullable=False),
        sa.Column("class_ref", sa.String(128), nullable=False),
        sa.Column("teacher_ref", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(8), nullable=False),
        sa.Column("draw_no", sa.SmallInteger()),
        sa.Column("policy_version", sa.String(48), nullable=False),
        sa.Column("eligibility_basis", sa.String(16), nullable=False),
        sa.Column("candidate_count", sa.SmallInteger(), nullable=False),
        sa.Column("candidate_set_hash", sa.String(64), nullable=False),
        sa.Column("selected_child_ref", sa.String(128)),
        sa.Column("class_revision", sa.Integer(), nullable=False),
        sa.Column("occurrence_revision", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("issued_at", _timestamp(), nullable=False),
        sa.Column("expires_at", _timestamp()),
        sa.Column("confirmed_at", _timestamp()),
        sa.Column("confirmed_by", sa.String(36)),
        sa.Column("confirmation_expires_at", _timestamp()),
        sa.Column("consumed_at", _timestamp()),
        sa.Column("consumed_run_ref", sa.String(128)),
        sa.Column("created_at", _timestamp(), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        TABLE,
        *_columns(),
        sa.ForeignKeyConstraint(
            ["occurrence_id"],
            [f"{SCHEMA}.occurrences.occurrence_id"],
            name="fk_sel_occurrence",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["plan_revision_id", "occurrence_id"],
            [f"{SCHEMA}.plan_revisions.plan_revision_id", f"{SCHEMA}.plan_revisions.occurrence_id"],
            name="fk_sel_plan",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("seq", name="uq_sel_seq"),
        *(sa.CheckConstraint(text, name=name) for name, text in CHECKS),
        schema=SCHEMA,
    )
    op.create_index(
        "uq_sel_live",
        TABLE,
        ["occurrence_id"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("state IN ('OPEN', 'CONFIRMED')"),
    )
    op.create_index(
        "uq_sel_draw",
        TABLE,
        ["occurrence_id", "draw_no"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("kind IN ('DRAW', 'RESELECT')"),
    )
    op.create_index(
        "uq_sel_consumed_run",
        TABLE,
        ["consumed_run_ref"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("consumed_run_ref IS NOT NULL"),
    )
    op.create_index(
        "ix_sel_occurrence",
        TABLE,
        ["occurrence_id", sa.text("seq DESC")],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_sel_child",
        TABLE,
        ["organization_ref", "selected_child_ref"],
        schema=SCHEMA,
        postgresql_where=sa.text("selected_child_ref IS NOT NULL"),
    )
    op.execute(FUNCTION_SQL)
    op.execute(
        f"CREATE TRIGGER {TRIGGER} BEFORE INSERT OR UPDATE OR DELETE ON {SCHEMA}.{TABLE} "
        f"FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.{FUNCTION}()"
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.execute(f"DROP TRIGGER {TRIGGER} ON {SCHEMA}.{TABLE}")
    op.execute(f"DROP FUNCTION {SCHEMA}.{FUNCTION}()")
    for index in ("ix_sel_child", "ix_sel_occurrence", "uq_sel_consumed_run", "uq_sel_draw"):
        op.drop_index(index, table_name=TABLE, schema=SCHEMA)
    op.drop_index("uq_sel_live", table_name=TABLE, schema=SCHEMA)
    op.drop_table(TABLE, schema=SCHEMA)
