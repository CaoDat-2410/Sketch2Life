"""FR-C-08 Parent StoryRun lifecycle: typed owner scope, DELETED, DELETE_RUN, nullable profile.

The single migration of the lifecycle DTR (Draft 6 §9). It lives on its own branch
(``frc08_lifecycle``) and depends on the Story head ``20261112_parent_story_context``, whose row
it replaces in ``alembic_version``. Deploy with ``upgrade heads``; a per-module
``upgrade <branch>@head`` skips this revision.

Order (DTR §9): §5.5 ``core_outbox_events`` and ``core_aggregate_revisions``, §5.1
``be1_data_lifecycle_requests``, §5.2 ``ai_jobs.cancellation_notice``, §5.3
``core_audit_entries`` (drop NOT NULL on ``organization_id``, add the scope columns, add the
CHECKs), then §5.4 the Story tables. Existing rows need no backfill: they become
``ORGANIZATION`` rows with a NULL scope ref. The CHECKs are added directly, which suits the
disposable verification database; a production rollout uses ``NOT VALID`` then ``VALIDATE``.

The downgrade refuses while any lifecycle data exists (DTR §9), otherwise it reverses every
step. Never run against ``sketch2life_m2_s1a``, ``be1_acceptance`` or ports 5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261119_frc08_lifecycle_scope"
down_revision = None
branch_labels = ("frc08_lifecycle",)
depends_on = ("20261112_parent_story_context",)

# DTR Draft 6 rule 1: the typed owner-scope CHECK of core_asset_metadata (S6).
OWNER_SCOPE_CHECK = (
    "(owner_scope_kind = 'PARENT_ACCOUNT' AND owner_scope_ref IS NOT NULL "
    "AND length(owner_scope_ref) > 0 "
    "AND organization_id IS NULL) OR "
    "(owner_scope_kind = 'ORGANIZATION' AND organization_id IS NOT NULL "
    "AND (owner_scope_ref IS NULL OR "
    "(length(owner_scope_ref) > 0 AND owner_scope_ref = organization_id)))"
)
PARENT_COMPLETED_CHECK = (
    "owner_scope_kind <> 'PARENT_ACCOUNT' OR state <> 'completed' OR "
    "(unresolved_items = 0 AND completed_at IS NOT NULL AND result_ref ~ "
    "'^lcr1;upload=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};ai=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};"
    "asset=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};story=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};"
    "sha256=[0-9a-f]{64}(;orph=[0-9]+)?$')"
)
NOTICE_RUN_REF_CHECK = "owner_scope_kind <> 'PARENT_ACCOUNT' OR story_run_ref IS NOT NULL"

# (table, schema, owner-scope CHECK name) in DTR §9 order.
SCOPED_TABLES: tuple[tuple[str, str | None, str], ...] = (
    ("core_outbox_events", None, "ck_core_outbox_owner_scope"),
    ("core_aggregate_revisions", None, "ck_core_aggregate_owner_scope"),
    ("be1_data_lifecycle_requests", None, "ck_be1_data_request_owner_scope"),
    ("cancellation_notice", "ai_jobs", "ck_cancellation_notice_owner_scope"),
    ("core_audit_entries", None, "ck_core_audit_owner_scope"),
)

RUN_STATES_BEFORE = (
    "'INPUT_PROCESSING','SUBJECT_REVIEW','PREPARATION_REVIEW',"
    "'SCRIPT_GENERATING','SCRIPT_GENERATION_UNKNOWN','SCRIPT_REVIEW',"
    "'VIDEO_ADMISSION_PENDING','DELETE_PENDING','FAILED','COMPLETED'"
)
RECEIPT_OPERATIONS_BEFORE = (
    "'CREATE_RUN','ATTACH_ASSET','CONFIRM_SUBJECT','CONFIRM_CONTEXT',"
    "'CANCEL_RUN','GENERATE_STORY_REVISION','CONFIRM_STORY_REVISION'"
)


def _organization_type(_table: str) -> sa.String:
    """Every one of the five tables stores ``organization_id`` as VARCHAR(128) (S1-S7)."""
    return sa.String(128)


def upgrade() -> None:
    for table, schema, check_name in SCOPED_TABLES:
        op.alter_column(
            table,
            "organization_id",
            schema=schema,
            existing_type=_organization_type(table),
            existing_nullable=False,
            nullable=True,
        )
        op.add_column(
            table,
            sa.Column(
                "owner_scope_kind",
                sa.String(32),
                nullable=False,
                server_default=sa.text("'ORGANIZATION'"),
            ),
            schema=schema,
        )
        op.add_column(
            table, sa.Column("owner_scope_ref", sa.String(128), nullable=True), schema=schema
        )
        if table == "cancellation_notice":
            op.add_column(
                table, sa.Column("story_run_ref", sa.String(128), nullable=True), schema=schema
            )
        op.create_check_constraint(check_name, table, OWNER_SCOPE_CHECK, schema=schema)
        if table == "be1_data_lifecycle_requests":
            op.create_check_constraint(
                "ck_be1_data_request_parent_completed", table, PARENT_COMPLETED_CHECK
            )
        if table == "cancellation_notice":
            op.create_check_constraint(
                "ck_cancellation_notice_parent_story_run_ref",
                table,
                NOTICE_RUN_REF_CHECK,
                schema=schema,
            )

    op.drop_constraint("ck_story_run_state", "runs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_state",
        "runs",
        f"run_state IN ({RUN_STATES_BEFORE},'DELETED')",
        schema="story",
    )
    op.alter_column(
        "runs",
        "profile_ref",
        schema="story",
        existing_type=sa.String(128),
        existing_nullable=False,
        nullable=True,
    )
    op.drop_constraint(
        "ck_story_receipt_operation", "command_receipts", schema="story", type_="check"
    )
    op.create_check_constraint(
        "ck_story_receipt_operation",
        "command_receipts",
        f"operation IN ({RECEIPT_OPERATIONS_BEFORE},'DELETE_RUN')",
        schema="story",
    )


DOWNGRADE_GUARD = """
DO $frc08_downgrade_guard$
BEGIN
    IF EXISTS (SELECT 1 FROM core_outbox_events
               WHERE owner_scope_kind = 'PARENT_ACCOUNT' OR owner_scope_ref IS NOT NULL)
       OR EXISTS (SELECT 1 FROM core_aggregate_revisions
               WHERE owner_scope_kind = 'PARENT_ACCOUNT' OR owner_scope_ref IS NOT NULL)
       OR EXISTS (SELECT 1 FROM be1_data_lifecycle_requests
               WHERE owner_scope_kind = 'PARENT_ACCOUNT' OR owner_scope_ref IS NOT NULL)
       OR EXISTS (SELECT 1 FROM ai_jobs.cancellation_notice
               WHERE owner_scope_kind = 'PARENT_ACCOUNT' OR owner_scope_ref IS NOT NULL)
       OR EXISTS (SELECT 1 FROM core_audit_entries
               WHERE owner_scope_kind = 'PARENT_ACCOUNT' OR owner_scope_ref IS NOT NULL)
    THEN
        RAISE EXCEPTION 'FR-C-08 downgrade refused: typed owner-scope rows exist';
    END IF;
    IF EXISTS (SELECT 1 FROM story.runs WHERE run_state = 'DELETED' OR profile_ref IS NULL) THEN
        RAISE EXCEPTION 'FR-C-08 downgrade refused: DELETED runs or NULL profile refs exist';
    END IF;
    IF EXISTS (SELECT 1 FROM story.command_receipts WHERE operation = 'DELETE_RUN') THEN
        RAISE EXCEPTION 'FR-C-08 downgrade refused: DELETE_RUN receipts exist';
    END IF;
END;
$frc08_downgrade_guard$;
"""


def downgrade() -> None:
    op.execute(sa.text(DOWNGRADE_GUARD))

    op.drop_constraint(
        "ck_story_receipt_operation", "command_receipts", schema="story", type_="check"
    )
    op.create_check_constraint(
        "ck_story_receipt_operation",
        "command_receipts",
        f"operation IN ({RECEIPT_OPERATIONS_BEFORE})",
        schema="story",
    )
    op.alter_column(
        "runs",
        "profile_ref",
        schema="story",
        existing_type=sa.String(128),
        existing_nullable=True,
        nullable=False,
    )
    op.drop_constraint("ck_story_run_state", "runs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_state", "runs", f"run_state IN ({RUN_STATES_BEFORE})", schema="story"
    )

    for table, schema, check_name in reversed(SCOPED_TABLES):
        if table == "cancellation_notice":
            op.drop_constraint(
                "ck_cancellation_notice_parent_story_run_ref",
                table,
                schema=schema,
                type_="check",
            )
        if table == "be1_data_lifecycle_requests":
            op.drop_constraint("ck_be1_data_request_parent_completed", table, type_="check")
        op.drop_constraint(check_name, table, schema=schema, type_="check")
        if table == "cancellation_notice":
            op.drop_column(table, "story_run_ref", schema=schema)
        op.drop_column(table, "owner_scope_ref", schema=schema)
        op.drop_column(table, "owner_scope_kind", schema=schema)
        op.alter_column(
            table,
            "organization_id",
            schema=schema,
            existing_type=_organization_type(table),
            existing_nullable=True,
            nullable=False,
        )
