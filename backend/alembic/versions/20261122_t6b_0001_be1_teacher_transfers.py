"""T-6b DDL: durable BE1 assignment transfer fence and receipt status."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261122_t6b_0001"
down_revision = "20261125_nt_0003"
branch_labels = None
depends_on = None

TABLE = "be1_teacher_assignment_transfers"
GUARD_FUNCTION = "guard_be1_teacher_assignment_transfer"
GUARD_TRIGGER = "trg_be1_teacher_assignment_transfer_guard"
PENDING_STATES = "'TRANSFER_PENDING','RECONCILE_REQUIRED'"
TERMINAL_STATES = "'COMPLETED','OFFBOARDED','COMPENSATED_CONFLICT'"

DOWNGRADE_GUARD = f"""
DO $t6b_be1_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM public.{TABLE}) THEN
        RAISE EXCEPTION 'T-6b BE1 downgrade refused - transfer history exists';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM public.be1_classrooms c
        WHERE c.assignment_revision > GREATEST(
            1,
            1 + (SELECT count(*) FROM public.be1_organization_assignments a
                 WHERE a.organization_id = c.organization_id
                   AND a.class_id = c.class_id AND a.role = 'teacher')
        )
    ) THEN
        RAISE EXCEPTION 'T-6b BE1 downgrade refused - assignment revision advanced';
    END IF;
    IF EXISTS (SELECT 1 FROM public.be1_command_receipts WHERE response_status <> 200) THEN
        RAISE EXCEPTION 'T-6b BE1 downgrade refused - accepted transfer receipt exists';
    END IF;
END;
$t6b_be1_downgrade_guard$;
"""

GUARD_SQL = f"""
CREATE FUNCTION public.{GUARD_FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF ROW(
       NEW.transfer_id, NEW.organization_id, NEW.class_id, NEW.action, NEW.principal_ref,
       NEW.old_subject, NEW.new_subject, NEW.old_assignment_id, NEW.new_assignment_id,
       NEW.expected_revision, NEW.fenced_revision, NEW.operation_scope,
       NEW.idempotency_key, NEW.fingerprint, NEW.created_at
     ) IS DISTINCT FROM ROW(
       OLD.transfer_id, OLD.organization_id, OLD.class_id, OLD.action, OLD.principal_ref,
       OLD.old_subject, OLD.new_subject, OLD.old_assignment_id, OLD.new_assignment_id,
       OLD.expected_revision, OLD.fenced_revision, OLD.operation_scope,
       OLD.idempotency_key, OLD.fingerprint, OLD.created_at
     ) THEN
    RAISE EXCEPTION 'BE1_TEACHER_TRANSFER_ENVELOPE_IMMUTABLE'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF OLD.state IN ({TERMINAL_STATES}) THEN
    RAISE EXCEPTION 'BE1_TEACHER_TRANSFER_TERMINAL_IMMUTABLE'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF NOT (
       (OLD.state = 'TRANSFER_PENDING' AND NEW.state IN
         ('RECONCILE_REQUIRED','COMPLETED','OFFBOARDED','COMPENSATED_CONFLICT'))
       OR (OLD.state = 'RECONCILE_REQUIRED' AND NEW.state IN
         ('RECONCILE_REQUIRED','COMPLETED','OFFBOARDED','COMPENSATED_CONFLICT'))
     ) THEN
    RAISE EXCEPTION 'BE1_TEACHER_TRANSFER_STATE_TRANSITION_INVALID'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF NEW.state_revision <> OLD.state_revision + 1
     OR NEW.attempt_count < OLD.attempt_count
     OR NEW.updated_at < OLD.updated_at THEN
    RAISE EXCEPTION 'BE1_TEACHER_TRANSFER_PROGRESS_INVALID'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF OLD.story_receipt_ref IS NOT NULL
     AND NEW.story_receipt_ref IS DISTINCT FROM OLD.story_receipt_ref THEN
    RAISE EXCEPTION 'BE1_TEACHER_TRANSFER_RECEIPT_IMMUTABLE'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  IF (NEW.state IN ({TERMINAL_STATES})) <> (NEW.finalized_at IS NOT NULL) THEN
    RAISE EXCEPTION 'BE1_TEACHER_TRANSFER_FINALIZED_SHAPE_INVALID'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  RETURN NEW;
END;
$$;
"""


def upgrade() -> None:
    op.add_column(
        "be1_classrooms",
        sa.Column("assignment_revision", sa.Integer(), server_default=sa.text("1"), nullable=False),
    )
    op.execute(
        sa.text(
            "UPDATE public.be1_classrooms c SET assignment_revision = GREATEST(1, 1 + "
            "(SELECT count(*) FROM public.be1_organization_assignments a "
            "WHERE a.organization_id = c.organization_id AND a.class_id = c.class_id "
            "AND a.role = 'teacher'))"
        )
    )
    op.create_check_constraint(
        "ck_be1_class_assignment_revision",
        "be1_classrooms",
        "assignment_revision >= 1",
    )
    op.add_column(
        "be1_command_receipts",
        sa.Column(
            "response_status",
            sa.SmallInteger(),
            server_default=sa.text("200"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_be1_command_receipt_status",
        "be1_command_receipts",
        "response_status BETWEEN 200 AND 299",
    )
    op.create_table(
        TABLE,
        sa.Column("transfer_id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("class_id", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("state", sa.String(length=24), nullable=False),
        sa.Column("principal_ref", sa.String(length=256), nullable=False),
        sa.Column("old_subject", sa.String(length=256), nullable=False),
        sa.Column("new_subject", sa.String(length=256), nullable=True),
        sa.Column("old_assignment_id", sa.String(length=36), nullable=False),
        sa.Column("new_assignment_id", sa.String(length=36), nullable=True),
        sa.Column("expected_revision", sa.Integer(), nullable=False),
        sa.Column("fenced_revision", sa.Integer(), nullable=False),
        sa.Column("operation_scope", sa.String(length=256), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("story_receipt_ref", sa.String(length=36), nullable=True),
        sa.Column("state_revision", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_failure_code", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("transfer_id", name="pk_be1_teacher_assignment_transfers"),
        sa.ForeignKeyConstraint(
            ["organization_id", "class_id"],
            ["be1_classrooms.organization_id", "be1_classrooms.class_id"],
            name="fk_be1_teacher_transfer_class",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["old_assignment_id"],
            ["be1_organization_assignments.assignment_id"],
            name="fk_be1_teacher_transfer_old_assignment",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["new_assignment_id"],
            ["be1_organization_assignments.assignment_id"],
            name="fk_be1_teacher_transfer_new_assignment",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["old_subject"],
            ["be1_adult_identities.subject"],
            name="fk_be1_teacher_transfer_old_subject",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["new_subject"],
            ["be1_adult_identities.subject"],
            name="fk_be1_teacher_transfer_new_subject",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "principal_ref",
            "operation_scope",
            "idempotency_key",
            name="uq_be1_teacher_transfer_idempotency",
        ),
        sa.CheckConstraint(
            "action IN ('REASSIGN','OFFBOARD')", name="ck_be1_teacher_transfer_action"
        ),
        sa.CheckConstraint(
            "state IN ('TRANSFER_PENDING','RECONCILE_REQUIRED','COMPLETED','OFFBOARDED',"
            "'COMPENSATED_CONFLICT')",
            name="ck_be1_teacher_transfer_state",
        ),
        sa.CheckConstraint(
            "expected_revision > 0 AND fenced_revision > 0",
            name="ck_be1_teacher_transfer_revisions",
        ),
        sa.CheckConstraint("state_revision > 0", name="ck_be1_teacher_transfer_state_revision"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_be1_teacher_transfer_attempt_count"),
        sa.CheckConstraint(
            "((action = 'OFFBOARD') = (new_assignment_id IS NULL)) AND "
            "((action = 'OFFBOARD') = (new_subject IS NULL))",
            name="ck_be1_teacher_transfer_new_assignment",
        ),
        sa.CheckConstraint(
            "length(idempotency_key) BETWEEN 1 AND 128 AND idempotency_key ~ '^[!-~]+$'",
            name="ck_be1_teacher_transfer_key",
        ),
        sa.CheckConstraint(
            "fingerprint ~ '^[0-9a-f]{64}$'", name="ck_be1_teacher_transfer_fingerprint"
        ),
    )
    op.create_index(
        "uq_be1_teacher_transfer_pending_class",
        TABLE,
        ["organization_id", "class_id"],
        unique=True,
        postgresql_where=sa.text(f"state IN ({PENDING_STATES})"),
    )
    op.create_index(
        "ix_be1_teacher_transfer_org_class_created",
        TABLE,
        ["organization_id", "class_id", "created_at"],
    )
    op.create_index(
        "ix_be1_teacher_transfer_state_updated",
        TABLE,
        ["state", "updated_at"],
    )
    op.execute(GUARD_SQL)
    op.execute(
        f"CREATE TRIGGER {GUARD_TRIGGER} BEFORE UPDATE ON public.{TABLE} "
        f"FOR EACH ROW EXECUTE FUNCTION public.{GUARD_FUNCTION}()"
    )


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))
    op.execute(f"DROP TRIGGER {GUARD_TRIGGER} ON public.{TABLE}")
    op.execute(f"DROP FUNCTION public.{GUARD_FUNCTION}()")
    op.drop_index("ix_be1_teacher_transfer_state_updated", table_name=TABLE)
    op.drop_index("ix_be1_teacher_transfer_org_class_created", table_name=TABLE)
    op.drop_index("uq_be1_teacher_transfer_pending_class", table_name=TABLE)
    op.drop_table(TABLE)
    op.drop_constraint(
        "ck_be1_command_receipt_status", "be1_command_receipts", type_="check"
    )
    op.drop_column("be1_command_receipts", "response_status")
    op.drop_constraint(
        "ck_be1_class_assignment_revision", "be1_classrooms", type_="check"
    )
    op.drop_column("be1_classrooms", "assignment_revision")


__all__ = ["GUARD_SQL", "DOWNGRADE_GUARD"]
