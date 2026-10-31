"""Create the independently owned synthetic vision pilot persistence branch."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261102_pv_0001"
down_revision = None
branch_labels = ("pilot_vision",)
depends_on = ("20261101_be1_age_0001", "20261015_ai_0001")

SCHEMA = "pilot_vision"


def upgrade() -> None:
    op.execute(sa.text(f'CREATE SCHEMA "{SCHEMA}"'))
    op.create_table(
        "request",
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("assistance_id", sa.String(length=256), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("semantic_identity", sa.String(length=128), nullable=False),
        sa.Column("operation_target", sa.String(length=512), nullable=False),
        sa.Column("debounce_key", sa.String(length=512), nullable=False),
        sa.Column("session_id", sa.String(length=256), nullable=False),
        sa.Column("target_key", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reservation", sa.String(length=32), nullable=True),
        sa.Column("counts_for_debounce", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("record_version > 0", name="ck_pv_request_version"),
        sa.PrimaryKeyConstraint("organization_id", "assistance_id"),
        schema=SCHEMA,
    )
    op.create_index(
        "uq_pv_request_active_semantic",
        "request",
        ["organization_id", "semantic_identity"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("status IN ('scheduling', 'scheduled')"),
    )
    op.create_table(
        "receipt",
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("principal_id", sa.String(length=256), nullable=False),
        sa.Column("contract_name", sa.String(length=256), nullable=False),
        sa.Column("target_id", sa.String(length=256), nullable=False),
        sa.Column("idempotency_key", sa.String(length=256), nullable=False),
        sa.Column("assistance_id", sa.String(length=256), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id", "assistance_id"],
            [f"{SCHEMA}.request.organization_id", f"{SCHEMA}.request.assistance_id"],
            ondelete="CASCADE",
            name="fk_pv_receipt_request",
        ),
        sa.PrimaryKeyConstraint(
            "organization_id", "principal_id", "contract_name", "target_id", "idempotency_key"
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "event",
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("event_id", sa.String(length=256), nullable=False),
        sa.Column("assistance_id", sa.String(length=256), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id", "assistance_id"],
            [f"{SCHEMA}.request.organization_id", f"{SCHEMA}.request.assistance_id"],
            ondelete="CASCADE",
            name="fk_pv_event_request",
        ),
        sa.PrimaryKeyConstraint("organization_id", "event_id"),
        schema=SCHEMA,
    )
    op.create_table(
        "notice",
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("notice_id", sa.String(length=256), nullable=False),
        sa.PrimaryKeyConstraint("organization_id", "notice_id"),
        schema=SCHEMA,
    )
    op.create_table(
        "epoch",
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("request_epoch", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("analysis_epoch", sa.BigInteger(), server_default="0", nullable=False),
        sa.CheckConstraint("request_epoch >= 0 AND analysis_epoch >= 0", name="ck_pv_epoch"),
        sa.PrimaryKeyConstraint("organization_id"),
        schema=SCHEMA,
    )
    op.create_table(
        "analysis_head",
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("analysis_id", sa.String(length=256), nullable=False),
        sa.Column("analysis_revision", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=256), nullable=False),
        sa.Column("attempt_id", sa.String(length=256), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("analysis_revision > 0", name="ck_pv_analysis_revision"),
        sa.PrimaryKeyConstraint("organization_id", "analysis_id"),
        sa.UniqueConstraint("job_id", "attempt_id", name="uq_pv_analysis_attempt"),
        schema=SCHEMA,
    )
    for table_name, constraint_name in (
        ("observation", "fk_pv_observation_head"),
        ("provider_result", "fk_pv_provider_result_head"),
    ):
        extra_columns = (
            [
                sa.Column("result_ref", sa.String(length=256), nullable=False),
                sa.Column("analysis_id", sa.String(length=256), nullable=False),
                sa.Column("result_sha256", sa.String(length=64), nullable=False),
                sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            ]
            if table_name == "provider_result"
            else [
                sa.Column("analysis_id", sa.String(length=256), nullable=False),
                sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            ]
        )
        primary_key = (
            ["organization_id", "result_ref"]
            if table_name == "provider_result"
            else ["organization_id", "analysis_id"]
        )
        op.create_table(
            table_name,
            sa.Column("organization_id", sa.String(length=128), nullable=False),
            *extra_columns,
            sa.ForeignKeyConstraint(
                ["organization_id", "analysis_id"],
                [f"{SCHEMA}.analysis_head.organization_id", f"{SCHEMA}.analysis_head.analysis_id"],
                ondelete="CASCADE",
                name=constraint_name,
            ),
            sa.PrimaryKeyConstraint(*primary_key),
            schema=SCHEMA,
        )
    op.create_table(
        "invocation",
        sa.Column("run_id", sa.String(length=256), nullable=False),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("job_id", sa.String(length=256), nullable=False),
        sa.Column("attempt_id", sa.String(length=256), nullable=False),
        sa.Column("state", sa.String(length=24), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_sha256", sa.String(length=64), nullable=True),
        sa.CheckConstraint(
            "state IN ('CLAIMED','SENT','SUCCEEDED','FAILED','UNKNOWN')",
            name="ck_pv_invocation_state",
        ),
        sa.CheckConstraint(
            "(state = 'CLAIMED' AND sent_at IS NULL AND finished_at IS NULL) OR "
            "(state = 'SENT' AND sent_at IS NOT NULL AND finished_at IS NULL) OR "
            "(state IN ('SUCCEEDED','FAILED','UNKNOWN') AND sent_at IS NOT NULL "
            "AND finished_at IS NOT NULL)",
            name="ck_pv_invocation_times",
        ),
        sa.PrimaryKeyConstraint("run_id"),
        sa.UniqueConstraint("job_id", "attempt_id", name="uq_pv_invocation_attempt"),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("invocation", schema=SCHEMA)
    op.drop_table("provider_result", schema=SCHEMA)
    op.drop_table("observation", schema=SCHEMA)
    op.drop_table("analysis_head", schema=SCHEMA)
    op.drop_table("epoch", schema=SCHEMA)
    op.drop_table("notice", schema=SCHEMA)
    op.drop_table("event", schema=SCHEMA)
    op.drop_table("receipt", schema=SCHEMA)
    op.drop_index("uq_pv_request_active_semantic", table_name="request", schema=SCHEMA)
    op.drop_table("request", schema=SCHEMA)
    op.execute(sa.text(f'DROP SCHEMA "{SCHEMA}"'))
