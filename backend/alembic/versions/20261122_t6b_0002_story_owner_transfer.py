"""T-6b DDL: immutable Story class binding, owner epochs and transfer receipt operation."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261122_t6b_0002"
down_revision = "20261125_as_0002"
branch_labels = None
depends_on = None

SCHEMA = "story"
RUNS = "runs"
RECEIPTS = "command_receipts"
FUNCTION = "guard_teacher_owner_epoch"
TRIGGER = "trg_story_run_teacher_owner_epoch"
LOCK_FREE_STATES = "'COMPLETED','FAILED','ABANDONED','DELETE_PENDING','DELETED'"

OLD_PINS_CHECK = "(occurrence_ref IS NULL) = (created_by_actor_ref IS NULL)"
NEW_PINS_CHECK = (
    "(occurrence_ref IS NULL) = (created_by_actor_ref IS NULL) AND "
    "(organization_ref IS NULL) = (class_ref IS NULL)"
)
NEW_BINDING_CHECK = (
    "occurrence_ref IS NULL OR (organization_ref IS NOT NULL AND class_ref IS NOT NULL)"
)
OLD_OWNER_CHECK = (
    "active_owner_teacher_id IS NULL OR (occurrence_ref IS NOT NULL "
    "AND actor_scope_kind = 'ORGANIZATION' AND active_owner_parent_account_id IS NULL)"
)
NEW_OWNER_CHECK = (
    "active_owner_teacher_id IS NULL OR (occurrence_ref IS NOT NULL "
    "AND organization_ref IS NOT NULL AND class_ref IS NOT NULL "
    "AND actor_scope_kind = 'ORGANIZATION' AND active_owner_parent_account_id IS NULL)"
)
OWNER_EPOCH_CHECK = "owner_epoch >= 0"
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
  IF ROW(NEW.occurrence_ref, NEW.organization_ref, NEW.class_ref, NEW.created_by_actor_ref)
     IS DISTINCT FROM ROW(OLD.occurrence_ref, OLD.organization_ref, OLD.class_ref,
                          OLD.created_by_actor_ref) THEN
    RAISE EXCEPTION 'STORY_TEACHER_OWNER_BINDING_IMMUTABLE'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF NEW.owner_epoch < OLD.owner_epoch THEN
    RAISE EXCEPTION 'STORY_TEACHER_OWNER_EPOCH_DECREASED'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF NEW.active_owner_teacher_id IS DISTINCT FROM OLD.active_owner_teacher_id THEN
    IF NEW.active_owner_teacher_id IS NULL AND NEW.run_state IN ({LOCK_FREE_STATES}) THEN
      IF NEW.owner_epoch <> OLD.owner_epoch THEN
        RAISE EXCEPTION 'STORY_TEACHER_OWNER_RELEASE_CHANGED_EPOCH'
          USING ERRCODE = 'integrity_constraint_violation';
      END IF;
    ELSE
      IF NEW.run_state IN ({LOCK_FREE_STATES}) OR NEW.owner_epoch <> OLD.owner_epoch + 1 THEN
        RAISE EXCEPTION 'STORY_TEACHER_OWNER_CHANGE_REQUIRES_NEXT_EPOCH'
          USING ERRCODE = 'integrity_constraint_violation';
      END IF;
    END IF;
  ELSIF NEW.owner_epoch <> OLD.owner_epoch THEN
    RAISE EXCEPTION 'STORY_TEACHER_OWNER_EPOCH_WITHOUT_OWNER_CHANGE'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  RETURN NEW;
END;
$$;
"""

DOWNGRADE_GUARD = f"""
DO $t6b_story_downgrade_guard$
BEGIN
    IF EXISTS (
        SELECT 1 FROM {SCHEMA}.{RUNS}
        WHERE active_owner_teacher_id IS NOT NULL
           OR occurrence_ref IS NOT NULL
           OR created_by_actor_ref IS NOT NULL
           OR organization_ref IS NOT NULL
           OR class_ref IS NOT NULL
           OR owner_epoch <> 0
    ) THEN
        RAISE EXCEPTION 'T-6b Story downgrade refused - Teacher-owned or bound runs exist';
    END IF;
    IF EXISTS (SELECT 1 FROM {SCHEMA}.{RECEIPTS} WHERE operation = 'TRANSFER_TEACHER_OWNER') THEN
        RAISE EXCEPTION 'T-6b Story downgrade refused - owner transfer receipts exist';
    END IF;
END;
$t6b_story_downgrade_guard$;
"""


def upgrade() -> None:
    op.add_column(RUNS, sa.Column("organization_ref", sa.String(length=128)), schema=SCHEMA)
    op.add_column(RUNS, sa.Column("class_ref", sa.String(length=128)), schema=SCHEMA)
    op.add_column(
        RUNS,
        sa.Column("owner_epoch", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        schema=SCHEMA,
    )
    # organization_ref and class_ref did not exist on the pre-T-6b StoryRun schema. Recover the
    # immutable binding from the occurrence before validating the new constraint, so valid
    # production Teacher runs already stored by the old schema remain upgradeable.
    op.execute(
        sa.text(
            f"""
            UPDATE {SCHEMA}.{RUNS} AS r
            SET organization_ref = o.organization_ref,
                class_ref = o.class_ref
            FROM lesson.occurrences AS o
            WHERE r.occurrence_ref = o.occurrence_id
              AND r.organization_ref IS NULL
              AND r.class_ref IS NULL;
            """
        )
    )
    op.execute(
        sa.text(
            f"""
            DO $t6b_story_binding_guard$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM {SCHEMA}.{RUNS}
                    WHERE (occurrence_ref IS NOT NULL OR created_by_actor_ref IS NOT NULL)
                      AND (organization_ref IS NULL OR class_ref IS NULL)
                ) THEN
                    RAISE EXCEPTION 'T-6b Story upgrade refused - unbound Teacher runs exist';
                END IF;
            END;
            $t6b_story_binding_guard$;
            """
        )
    )
    op.drop_constraint("ck_story_run_teacher_pins", RUNS, schema=SCHEMA, type_="check")
    op.drop_constraint("ck_story_run_teacher_owner", RUNS, schema=SCHEMA, type_="check")
    op.create_check_constraint("ck_story_run_teacher_pins", RUNS, NEW_PINS_CHECK, schema=SCHEMA)
    op.create_check_constraint(
        "ck_story_run_teacher_binding", RUNS, NEW_BINDING_CHECK, schema=SCHEMA
    )
    op.create_check_constraint("ck_story_run_teacher_owner", RUNS, NEW_OWNER_CHECK, schema=SCHEMA)
    op.create_check_constraint(
        "ck_story_run_owner_epoch", RUNS, OWNER_EPOCH_CHECK, schema=SCHEMA
    )
    op.create_index(
        "ix_story_run_teacher_class_owner",
        RUNS,
        ["organization_ref", "class_ref", "active_owner_teacher_id"],
        schema=SCHEMA,
        postgresql_where=sa.text("active_owner_teacher_id IS NOT NULL"),
    )
    op.execute(GUARD_SQL)
    op.execute(
        f"CREATE TRIGGER {TRIGGER} BEFORE UPDATE OF active_owner_teacher_id, owner_epoch, "
        f"run_state, occurrence_ref, organization_ref, class_ref, created_by_actor_ref "
        f"ON {SCHEMA}.{RUNS} FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.{FUNCTION}()"
    )
    op.drop_constraint("ck_story_receipt_operation", RECEIPTS, schema=SCHEMA, type_="check")
    op.create_check_constraint(
        "ck_story_receipt_operation",
        RECEIPTS,
        _receipt_operation_check(FINAL_RECEIPT_OPERATIONS),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.drop_constraint("ck_story_receipt_operation", RECEIPTS, schema=SCHEMA, type_="check")
    op.create_check_constraint(
        "ck_story_receipt_operation",
        RECEIPTS,
        _receipt_operation_check(RECEIPT_OPERATIONS_BEFORE),
        schema=SCHEMA,
    )
    op.execute(f"DROP TRIGGER {TRIGGER} ON {SCHEMA}.{RUNS}")
    op.execute(f"DROP FUNCTION {SCHEMA}.{FUNCTION}()")
    op.drop_index("ix_story_run_teacher_class_owner", table_name=RUNS, schema=SCHEMA)
    op.drop_constraint("ck_story_run_owner_epoch", RUNS, schema=SCHEMA, type_="check")
    op.drop_constraint("ck_story_run_teacher_owner", RUNS, schema=SCHEMA, type_="check")
    op.create_check_constraint("ck_story_run_teacher_owner", RUNS, OLD_OWNER_CHECK, schema=SCHEMA)
    op.drop_constraint("ck_story_run_teacher_binding", RUNS, schema=SCHEMA, type_="check")
    op.drop_constraint("ck_story_run_teacher_pins", RUNS, schema=SCHEMA, type_="check")
    op.create_check_constraint("ck_story_run_teacher_pins", RUNS, OLD_PINS_CHECK, schema=SCHEMA)
    op.drop_column(RUNS, "owner_epoch", schema=SCHEMA)
    op.drop_column(RUNS, "class_ref", schema=SCHEMA)
    op.drop_column(RUNS, "organization_ref", schema=SCHEMA)


__all__ = [
    "DOWNGRADE_GUARD",
    "GUARD_SQL",
    "NEW_BINDING_CHECK",
    "NEW_OWNER_CHECK",
    "NEW_PINS_CHECK",
    "OLD_OWNER_CHECK",
    "OLD_PINS_CHECK",
    "OWNER_EPOCH_CHECK",
    "RECEIPT_OPERATIONS_AFTER",
    "RECEIPT_OPERATIONS_BEFORE",
]
