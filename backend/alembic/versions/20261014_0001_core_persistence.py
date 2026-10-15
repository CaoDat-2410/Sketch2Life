"""Create durable core records, receipts, audit and outbox."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261014_0001"
down_revision = None
branch_labels = ("be1_core",)
depends_on = None


def upgrade() -> None:
    op.create_table(
        "core_aggregate_revisions",
        sa.Column("aggregate_id", sa.String(length=128), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("revision", sa.BigInteger(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("revision > 0", name="ck_core_aggregate_revision_positive"),
    )
    op.create_index(
        "ix_core_aggregate_revisions_organization_id",
        "core_aggregate_revisions",
        ["organization_id"],
    )

    op.create_table(
        "core_canvas_operations",
        sa.Column("operation_id", sa.String(length=128), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column(
            "canvas_id",
            sa.String(length=128),
            sa.ForeignKey("core_aggregate_revisions.aggregate_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("turn_id", sa.String(length=128), nullable=False),
        sa.Column("participant_id", sa.String(length=128), nullable=False),
        sa.Column("document_epoch", sa.Integer(), nullable=False),
        sa.Column("resulting_revision", sa.BigInteger(), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("document_epoch > 0", name="ck_core_operation_epoch_positive"),
        sa.CheckConstraint("resulting_revision > 0", name="ck_core_operation_revision_positive"),
        sa.CheckConstraint(
            "length(request_fingerprint) = 64",
            name="ck_core_operation_fingerprint_length",
        ),
        sa.UniqueConstraint(
            "canvas_id",
            "document_epoch",
            "resulting_revision",
            name="uq_core_canvas_epoch_revision",
        ),
    )
    op.create_index(
        "ix_core_operation_canvas_epoch_revision",
        "core_canvas_operations",
        ["canvas_id", "document_epoch", "resulting_revision"],
    )

    op.create_table(
        "core_idempotency_receipts",
        sa.Column("organization_id", sa.String(length=128), primary_key=True),
        sa.Column("scope", sa.String(length=256), primary_key=True),
        sa.Column("key", sa.String(length=256), primary_key=True),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("resulting_revision", sa.BigInteger(), nullable=False),
        sa.Column(
            "operation_id",
            sa.String(length=128),
            sa.ForeignKey("core_canvas_operations.operation_id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("resulting_revision > 0", name="ck_core_receipt_revision_positive"),
        sa.CheckConstraint(
            "length(request_fingerprint) = 64",
            name="ck_core_receipt_fingerprint_length",
        ),
    )

    op.create_table(
        "core_canvas_checkpoints",
        sa.Column("checkpoint_id", sa.String(length=128), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column(
            "canvas_id",
            sa.String(length=128),
            sa.ForeignKey("core_aggregate_revisions.aggregate_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("document_epoch", sa.Integer(), nullable=False),
        sa.Column("revision", sa.BigInteger(), nullable=False),
        sa.Column(
            "through_operation_id",
            sa.String(length=128),
            sa.ForeignKey("core_canvas_operations.operation_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_ref", sa.String(length=512), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("document_epoch > 0", name="ck_core_checkpoint_epoch_positive"),
        sa.CheckConstraint("revision > 0", name="ck_core_checkpoint_revision_positive"),
        sa.CheckConstraint(
            "length(checksum_sha256) = 64",
            name="ck_core_checkpoint_checksum_length",
        ),
        sa.UniqueConstraint(
            "canvas_id", "document_epoch", "revision", name="uq_core_checkpoint_revision"
        ),
    )
    op.create_index(
        "ix_core_checkpoint_canvas_latest",
        "core_canvas_checkpoints",
        ["canvas_id", "document_epoch", "revision"],
    )

    op.create_table(
        "core_asset_metadata",
        sa.Column("asset_ref", sa.String(length=256), primary_key=True),
        sa.Column("asset_version", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("media_type", sa.String(length=128), nullable=False),
        sa.Column("source_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("derived_from_ref", sa.String(length=256), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("asset_version > 0", name="ck_core_asset_version_positive"),
        sa.CheckConstraint("length(content_sha256) = 64", name="ck_core_asset_hash_length"),
    )
    op.create_index(
        "ix_core_asset_organization", "core_asset_metadata", ["organization_id", "asset_ref"]
    )

    op.create_table(
        "core_audit_entries",
        sa.Column("audit_id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("actor_ref", sa.String(length=128), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=256), nullable=False),
        sa.Column("decision", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_core_audit_org_created", "core_audit_entries", ["organization_id", "created_at"]
    )
    op.create_index(
        "ix_core_audit_resource_created", "core_audit_entries", ["resource_id", "created_at"]
    )

    op.create_table(
        "core_outbox_events",
        sa.Column("event_id", sa.String(length=36), primary_key=True),
        sa.Column("event_type", sa.String(length=160), nullable=False),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column(
            "aggregate_id",
            sa.String(length=128),
            sa.ForeignKey("core_aggregate_revisions.aggregate_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("aggregate_revision", sa.BigInteger(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("lease_owner", sa.String(length=128), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("aggregate_revision > 0", name="ck_core_outbox_revision_positive"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_core_outbox_attempt_nonnegative"),
        sa.CheckConstraint(
            "status IN ('pending', 'leased', 'delivered')",
            name="ck_core_outbox_status_valid",
        ),
        sa.CheckConstraint(
            "status != 'leased' OR (lease_owner IS NOT NULL AND lease_until IS NOT NULL)",
            name="ck_core_outbox_lease_complete",
        ),
    )
    op.create_index(
        "ix_core_outbox_ready",
        "core_outbox_events",
        ["status", "available_at", "created_at"],
    )
    op.create_index("ix_core_outbox_lease", "core_outbox_events", ["status", "lease_until"])

    op.create_table(
        "core_outbox_consumer_receipts",
        sa.Column("consumer_name", sa.String(length=128), primary_key=True),
        sa.Column(
            "event_id",
            sa.String(length=36),
            sa.ForeignKey("core_outbox_events.event_id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("core_outbox_consumer_receipts")
    op.drop_index("ix_core_outbox_lease", table_name="core_outbox_events")
    op.drop_index("ix_core_outbox_ready", table_name="core_outbox_events")
    op.drop_table("core_outbox_events")
    op.drop_index("ix_core_audit_resource_created", table_name="core_audit_entries")
    op.drop_index("ix_core_audit_org_created", table_name="core_audit_entries")
    op.drop_table("core_audit_entries")
    op.drop_index("ix_core_asset_organization", table_name="core_asset_metadata")
    op.drop_table("core_asset_metadata")
    op.drop_index("ix_core_checkpoint_canvas_latest", table_name="core_canvas_checkpoints")
    op.drop_table("core_canvas_checkpoints")
    op.drop_table("core_idempotency_receipts")
    op.drop_index("ix_core_operation_canvas_epoch_revision", table_name="core_canvas_operations")
    op.drop_table("core_canvas_operations")
    op.drop_index(
        "ix_core_aggregate_revisions_organization_id", table_name="core_aggregate_revisions"
    )
    op.drop_table("core_aggregate_revisions")
