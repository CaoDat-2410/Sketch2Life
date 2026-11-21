"""Durable identity permissions and metadata-only Admin communication records."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from sketch2life.infrastructure.persistence.core_models import CorePersistenceBase

JSON_DOCUMENT = JSON().with_variant(JSONB(), "postgresql")


class PermissionGrantModel(CorePersistenceBase):
    __tablename__ = "identity_permission_grants"
    __table_args__ = (
        CheckConstraint("permission = 'content_admin'", name="ck_identity_permission_name"),
        CheckConstraint("revision > 0", name="ck_identity_permission_revision"),
    )
    subject: Mapped[str] = mapped_column(String(256), primary_key=True)
    permission: Mapped[str] = mapped_column(String(64), primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    granted_by: Mapped[str] = mapped_column(String(256), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AdminCommandReceiptModel(CorePersistenceBase):
    __tablename__ = "platform_command_receipts"
    actor_ref: Mapped[str] = mapped_column(String(256), primary_key=True)
    operation: Mapped[str] = mapped_column(String(200), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    response_json: Mapped[dict] = mapped_column(JSON_DOCUMENT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InboxItemModel(CorePersistenceBase):
    __tablename__ = "notification_inbox_items"
    __table_args__ = (Index("ix_notification_recipient_created", "recipient_ref", "created_at"),)
    item_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    recipient_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmailDeliveryModel(CorePersistenceBase):
    """An outbox intent; Firebase action links and credentials are never stored."""

    __tablename__ = "notification_email_deliveries"
    __table_args__ = (
        CheckConstraint(
            "state IN ('pending','sending','sent','failed')", name="ck_email_delivery_state"
        ),
        Index("ix_email_pending", "state", "created_at"),
    )
    delivery_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    recipient_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    template: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AccountPreferenceModel(CorePersistenceBase):
    __tablename__ = "identity_account_preferences"
    subject: Mapped[str] = mapped_column(String(256), primary_key=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="vi-VN")
    email_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class AuditRetentionPolicyModel(CorePersistenceBase):
    __tablename__ = "platform_audit_retention_policies"
    __table_args__ = (
        CheckConstraint("policy_key = 'platform'", name="ck_audit_retention_single_policy"),
        CheckConstraint("revision > 0", name="ck_audit_retention_revision"),
        CheckConstraint(
            "retention_days IS NULL OR retention_days > 0", name="ck_audit_retention_days"
        ),
    )
    policy_key: Mapped[str] = mapped_column(String(24), primary_key=True)
    retention_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_by: Mapped[str] = mapped_column(String(256), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_purged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_purged_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )


PLATFORM_TABLES = [
    PermissionGrantModel.__table__,
    AdminCommandReceiptModel.__table__,
    InboxItemModel.__table__,
    EmailDeliveryModel.__table__,
    AccountPreferenceModel.__table__,
]
