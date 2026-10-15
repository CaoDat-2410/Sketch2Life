"""SQLAlchemy mappings for BE1-02's PostgreSQL core records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class CorePersistenceBase(DeclarativeBase):
    """Metadata for the new core persistence boundary."""


class CoreAggregateRevisionModel(CorePersistenceBase):
    __tablename__ = "core_aggregate_revisions"
    __table_args__ = (CheckConstraint("revision > 0", name="ck_core_aggregate_revision_positive"),)

    aggregate_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    revision: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}


class CoreCanvasOperationModel(CorePersistenceBase):
    __tablename__ = "core_canvas_operations"
    __table_args__ = (
        UniqueConstraint(
            "canvas_id",
            "document_epoch",
            "resulting_revision",
            name="uq_core_canvas_epoch_revision",
        ),
        CheckConstraint("document_epoch > 0", name="ck_core_operation_epoch_positive"),
        CheckConstraint("resulting_revision > 0", name="ck_core_operation_revision_positive"),
        CheckConstraint(
            "length(request_fingerprint) = 64",
            name="ck_core_operation_fingerprint_length",
        ),
        Index(
            "ix_core_operation_canvas_epoch_revision",
            "canvas_id",
            "document_epoch",
            "resulting_revision",
        ),
    )

    operation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    canvas_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("core_aggregate_revisions.aggregate_id", ondelete="RESTRICT"),
        nullable=False,
    )
    session_id: Mapped[str] = mapped_column(String(128), nullable=False)
    turn_id: Mapped[str] = mapped_column(String(128), nullable=False)
    participant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    document_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    resulting_revision: Mapped[int] = mapped_column(BigInteger, nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    operation_payload: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CoreIdempotencyReceiptModel(CorePersistenceBase):
    __tablename__ = "core_idempotency_receipts"
    __table_args__ = (
        CheckConstraint("resulting_revision > 0", name="ck_core_receipt_revision_positive"),
        CheckConstraint(
            "length(request_fingerprint) = 64", name="ck_core_receipt_fingerprint_length"
        ),
    )

    organization_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    scope: Mapped[str] = mapped_column(String(256), primary_key=True)
    key: Mapped[str] = mapped_column(String(256), primary_key=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    resulting_revision: Mapped[int] = mapped_column(BigInteger, nullable=False)
    operation_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("core_canvas_operations.operation_id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CoreCanvasCheckpointModel(CorePersistenceBase):
    __tablename__ = "core_canvas_checkpoints"
    __table_args__ = (
        UniqueConstraint(
            "canvas_id", "document_epoch", "revision", name="uq_core_checkpoint_revision"
        ),
        CheckConstraint("document_epoch > 0", name="ck_core_checkpoint_epoch_positive"),
        CheckConstraint("revision > 0", name="ck_core_checkpoint_revision_positive"),
        CheckConstraint("length(checksum_sha256) = 64", name="ck_core_checkpoint_checksum_length"),
        Index("ix_core_checkpoint_canvas_latest", "canvas_id", "document_epoch", "revision"),
    )

    checkpoint_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    canvas_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("core_aggregate_revisions.aggregate_id", ondelete="RESTRICT"),
        nullable=False,
    )
    document_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    revision: Mapped[int] = mapped_column(BigInteger, nullable=False)
    through_operation_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("core_canvas_operations.operation_id", ondelete="RESTRICT"),
        nullable=False,
    )
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CoreAssetMetadataModel(CorePersistenceBase):
    __tablename__ = "core_asset_metadata"
    __table_args__ = (
        CheckConstraint("asset_version > 0", name="ck_core_asset_version_positive"),
        CheckConstraint("length(content_sha256) = 64", name="ck_core_asset_hash_length"),
        Index("ix_core_asset_organization", "organization_id", "asset_ref"),
    )

    asset_ref: Mapped[str] = mapped_column(String(256), primary_key=True)
    asset_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    media_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_refs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    derived_from_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CoreAuditEntryModel(CorePersistenceBase):
    __tablename__ = "core_audit_entries"
    __table_args__ = (
        Index("ix_core_audit_org_created", "organization_id", "created_at"),
        Index("ix_core_audit_resource_created", "resource_id", "created_at"),
    )

    audit_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(256), nullable=False)
    decision: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CoreOutboxEventModel(CorePersistenceBase):
    __tablename__ = "core_outbox_events"
    __table_args__ = (
        CheckConstraint("aggregate_revision > 0", name="ck_core_outbox_revision_positive"),
        CheckConstraint("attempt_count >= 0", name="ck_core_outbox_attempt_nonnegative"),
        CheckConstraint(
            "status IN ('pending', 'leased', 'delivered')",
            name="ck_core_outbox_status_valid",
        ),
        CheckConstraint(
            "status != 'leased' OR (lease_owner IS NOT NULL AND lease_until IS NOT NULL)",
            name="ck_core_outbox_lease_complete",
        ),
        Index("ix_core_outbox_ready", "status", "available_at", "created_at"),
        Index("ix_core_outbox_lease", "status", "lease_until"),
    )

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(160), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("core_aggregate_revisions.aggregate_id", ondelete="RESTRICT"),
        nullable=False,
    )
    aggregate_revision: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payload: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CoreOutboxConsumerReceiptModel(CorePersistenceBase):
    __tablename__ = "core_outbox_consumer_receipts"

    consumer_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("core_outbox_events.event_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


__all__ = [
    "CoreAggregateRevisionModel",
    "CoreAssetMetadataModel",
    "CoreAuditEntryModel",
    "CoreCanvasCheckpointModel",
    "CoreCanvasOperationModel",
    "CoreIdempotencyReceiptModel",
    "CoreOutboxConsumerReceiptModel",
    "CoreOutboxEventModel",
    "CorePersistenceBase",
]
